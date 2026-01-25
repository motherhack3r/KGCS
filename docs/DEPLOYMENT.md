# KGCS Deployment & Setup Guide

**Purpose:** Instructions for setting up KGCS locally and in production.

---

## Local Development Setup

### Prerequisites

- Python 3.10+
- Git
- Neo4j (Docker recommended)
- Virtual environment tool (venv or conda)

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/kgcs.git
cd kgcs
```

### Step 2: Create Virtual Environment

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# OR using conda
conda create -n kgcs python=3.10
conda activate kgcs
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Current dependencies:**
- `rdflib>=6.0.0` — RDF/Turtle handling
- `pyshacl>=0.20.0` — SHACL validation
- `neo4j>=5.0.0` — Neo4j driver
- `python-dateutil>=2.8.0` — Date parsing
- `aiohttp` — Async HTTP (for data ingestion)

### Step 4: Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env`:

```
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password_here
NEO4J_DATABASE=neo4j
NEO4J_ENCRYPTED=false
NEO4J_AUTH_ENABLED=true

# ETL Configuration
ETL_BATCH_SIZE=1000
ETL_PARALLELISM=4
ETL_TIMEOUT_SECONDS=300
```

### Step 5: Start Neo4j (Docker)

```bash
# Create volume for persistence
docker volume create neo4j-data

# Start Neo4j 5.x
docker run -d \
  --name neo4j \
  -p 7687:7687 \
  -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/your_password_here \
  -v neo4j-data:/data \
  neo4j:5.13-community

# Verify
docker logs neo4j
```

Access Neo4j Browser: http://localhost:7474

### Step 6: Verify Installation

```bash
# Test SHACL validation
python scripts/validate_shacl_stream.py \
  --data data/cpe/samples/sample_cpe.json \
  --shapes docs/ontology/shacl/cpe-shapes.ttl

# Run ETL test
pytest tests/test_etl_pipeline.py -v

# Run comprehensive tests
pytest tests/test_phase3_comprehensive.py -v
```

---

## Local Data Ingestion

### Ingest CPE Sample Data

```bash
# Transform JSON to RDF
python -m src.etl.etl_cpe \
  --input data/cpe/samples/sample_cpe.json \
  --output tmp/cpe-output.ttl \
  --validate

# Load into Neo4j (pending Phase 3 MVP)
python src/etl/rdf_to_neo4j.py \
  --ttl tmp/cpe-output.ttl \
  --batch-size 1000
```

### Ingest All Standards (Full Phase 3)

```bash
# Orchestrator (validates each ETL + SHACL)
python scripts/validate_etl_pipeline_order.py
```

---

## Docker Compose (Complete Stack)

Create `docker-compose.yml`:

```yaml
version: '3.9'

services:
  neo4j:
    image: neo4j:5.13-community
    container_name: kgcs-neo4j
    ports:
      - "7687:7687"     # Bolt
      - "7474:7474"     # Browser
    environment:
      NEO4J_AUTH: neo4j/your_password_here
      NEO4J_server_logs_debug: "DEBUG"
    volumes:
      - neo4j-data:/data
      - neo4j-logs:/logs
    healthcheck:
      test: ["CMD-SHELL", "echo RETURN 1 | cypher-shell -a bolt://neo4j:7687 || exit 1"]
      interval: 5s
      timeout: 5s
      retries: 5

  kgcs:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: kgcs-app
    depends_on:
      neo4j:
        condition: service_healthy
    environment:
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: your_password_here
    volumes:
      - ./data:/app/data:ro
      - ./tmp:/app/tmp
      - ./artifacts:/app/artifacts
    command: |
      sh -c "
        python scripts/validate_etl_pipeline_order.py &&
        python src/etl/rdf_to_neo4j.py --ttl tmp/cpe-output.ttl
      "

volumes:
  neo4j-data:
  neo4j-logs:
```

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "scripts/validate_etl_pipeline_order.py"]
```

Start the stack:

```bash
docker-compose up -d
```

---

## Production Deployment

### Architecture

```
Data Ingestion Pipeline
  ├─ Download NVD + MITRE data
  ├─ ETL Transform (JSON → RDF)
  ├─ SHACL Validate
  ├─ Load Neo4j (RDF → Cypher)
  └─ Query API (REST/GraphQL)
    └─ LLM Integration
```

### Infrastructure Requirements

| Component | Min | Recommended | Notes |
| --- | --- | --- | --- |
| **CPU** | 4 cores | 16 cores | Neo4j + ETL parallelism |
| **RAM** | 16 GB | 64 GB | Neo4j heap + ETL working space |
| **Storage** | 500 GB | 2 TB | RDF + Neo4j database |
| **Network** | 1 Gbps | 10 Gbps | Large data transfers |

### Neo4j Configuration (Production)

Edit `docker-compose.yml` for production:

```yaml
neo4j:
  image: neo4j:5.13-enterprise  # Use enterprise for HA
  environment:
    NEO4J_AUTH: neo4j/strong_password_here
    NEO4J_server_memory_heap_initial__size: 32g
    NEO4J_server_memory_heap_max__size: 32g
    NEO4J_server_memory_pagecache_size: 16g
    NEO4J_dbms_security_auth__enabled: true
    NEO4J_ACCEPT_LICENSE_AGREEMENT: "yes"
    # Backup settings
    NEO4J_dbms_backup_enabled: "true"
  volumes:
    - neo4j-data:/data
    - neo4j-logs:/logs
    - neo4j-backups:/backups
```

### Backup Strategy

```bash
# Daily backup (cron job)
0 2 * * * neo4j-admin database backup --to-path=/backups neo4j-backup-$(date +\%Y\%m\%d).db

# Restore from backup
neo4j-admin database restore neo4j-backup-20260125.db
```

### Monitoring

Use Neo4j's built-in monitoring:

```
http://localhost:7474/browser/
  → DBMS Monitor → Databases → neo4j
```

Query database stats:

```cypher
CALL dbms.queryJmx("org.neo4j:instance=kernel#0,name=Store sizes") YIELD attributes
RETURN attributes;
```

### CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy KGCS

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'docs/ontology/**'
      - 'scripts/**'
      - 'requirements.txt'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
      - run: python scripts/validate_etl_pipeline_order.py

  validate-shacl:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install pyshacl rdflib
      - run: python scripts/validate_shacl_stream.py --data data/*/samples/*.ttl

  deploy:
    needs: [test, validate-shacl]
    runs-on: ubuntu-latest
    if: success()
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t kgcs:latest .
      - name: Push to registry
        run: docker push your-registry/kgcs:latest
      - name: Deploy to production
        run: |
          ssh prod-server "cd /opt/kgcs && \
            docker-compose pull && \
            docker-compose up -d && \
            docker-compose exec neo4j neo4j-admin database dump neo4j"
```

---

## Operational Tasks

### Weekly Data Refresh

```bash
#!/bin/bash
# Scheduled weekly ETL (cron: 0 2 * * 0 /opt/kgcs/weekly-refresh.sh)

cd /opt/kgcs

# Download latest NVD data
curl -O https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json

# Transform + Validate + Load
python scripts/validate_etl_pipeline_order.py

# Backup
docker exec kgcs-neo4j neo4j-admin database backup neo4j /backups/neo4j-$(date +%Y%m%d).db
```

### Monitor Data Freshness

```cypher
// Query to check latest data ingest timestamp
MATCH (c:CVE)
RETURN c.cveId, c.cveLastModifiedDate
ORDER BY c.cveLastModifiedDate DESC
LIMIT 10;
```

### Query Performance Tuning

```cypher
// Create indexes for fast lookups
CREATE INDEX idx_cve_id FOR (c:CVE) ON (c.cveId);
CREATE INDEX idx_cpe_uri FOR (p:Platform) ON (p.cpeUri);
CREATE INDEX idx_cwe_id FOR (w:CWE) ON (w.cweId);
CREATE INDEX idx_technique_id FOR (t:Technique) ON (t.techniqueId);

// Check existing indexes
SHOW INDEXES;
```

---

## Troubleshooting

### Neo4j Won't Connect

```bash
# Check Neo4j logs
docker logs kgcs-neo4j

# Verify connectivity
docker exec kgcs-neo4j cypher-shell -u neo4j -p your_password "RETURN 1"
```

### SHACL Validation Failures

```bash
# Validate specific file with detailed output
python scripts/validate_shacl_stream.py \
  --data tmp/output.ttl \
  --shapes docs/ontology/shacl/*-shapes.ttl \
  --output artifacts/debug
```

See `artifacts/shacl-report-*.json` for failure details.

### ETL Timeout (Large Files)

```python
# Increase timeout in src/config.py
ETLConfig(timeout_seconds=600)  # 10 minutes

# Or use streaming validation
python scripts/validate_shacl_stream.py \
  --data large-file.ttl \
  --chunk-size 5000
```

---

## Security Considerations

### Authentication

- Change default Neo4j password immediately
- Use strong passwords (16+ chars, mixed case + numbers)
- Enable SSL/TLS for Neo4j connections

### Network

- Neo4j bolt port (7687) should not be exposed publicly
- Use VPN or firewall rules for remote access
- Query API (if deployed) should be behind API gateway

### Data

- Backup strategy: daily backups to secure storage
- Encryption at rest: enable Neo4j enterprise encryption
- Audit logging: enable Neo4j query logging for compliance

---

## Performance Benchmarks

Tested on:
- 4 CPU cores, 16 GB RAM
- CPE: 217 MB (~400K entries)
- CVE: 5 MB (~10K entries)

| Operation | Time | Notes |
| --- | --- | --- |
| CPE ETL | 15 min | Streaming validator |
| CVE ETL | 3 min | SHACL validation included |
| Neo4j Load | 12 min | CPE + CVE, batch_size=1000 |
| Query (Causal Chain) | <100 ms | Full path: CPE → CVE → CWE → ... |

---

## Support & References

- [ARCHITECTURE.md](ARCHITECTURE.md) — Phases and roadmap
- [GOVERNANCE.md](ontology/GOVERNANCE.md) — Data policies
- Neo4j Docs: https://neo4j.com/docs/
- Docker Docs: https://docs.docker.com/
- GitHub Actions: https://docs.github.com/en/actions

