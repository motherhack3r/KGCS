# Configuration Guide

This document explains how to configure KGCS for local development and production use.

## Quick Start

1. **Copy the template:**

    ```bash
    cp .env.example .env
    ```

2. **Edit `.env` with your Neo4j credentials:**

    ```bash
    # Linux/Mac
    nano .env

    # Windows PowerShell
    notepad .env
    ```

3. **Set your Neo4j connection details:**

    ```env
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=your-password-here
    NEO4J_DATABASE=neo4j
    ```

4. **Test the configuration:**

    ```bash
    python -m src.config
    ```

## Configuration Hierarchy

KGCS loads configuration in this order (highest priority last):

1. Default values in `src/config.py`
2. Environment variables
3. Variables from `.env` file

## Configuration File

### `.env` (Local Secrets - NOT COMMITTED)

Contains actual credentials and sensitive settings:

```env
NEO4J_PASSWORD=your-actual-password
NEO4J_URI=bolt://your-server:7687
```

**IMPORTANT:** `.env` is in `.gitignore` and should NEVER be committed to git.

### `.env.example` (Template - COMMITTED)

Safe template for developers to copy and customize:

```env
NEO4J_PASSWORD=your-secure-password-here
NEO4J_URI=bolt://localhost:7687
```

This file IS committed so all developers know what keys are needed.

## Neo4j Configuration

### Required Settings

```env
NEO4J_URI=bolt://localhost:7687          # Connection URI
NEO4J_USER=neo4j                          # Username
NEO4J_PASSWORD=your-password              # Password (NEVER share!)
NEO4J_DATABASE=neo4j                      # Database name
```

### Optional Settings

```env
NEO4J_ENCRYPTED=false                     # Use encrypted connection
NEO4J_TRUST=TRUST_ALL_CERTIFICATES        # Certificate trust mode
NEO4J_AUTH_ENABLED=true                   # Enable authentication
```

### Common URIs

- **Local Development:** `bolt://localhost:7687`
- **Docker Container:** `bolt://neo4j:7687`
- **Remote Server:** `bolt://server.example.com:7687`

## ETL Configuration

```env
ETL_BATCH_SIZE=1000              # Records to process per batch
ETL_PARALLELISM=4                # Number of parallel workers
ETL_TIMEOUT_SECONDS=300          # Timeout for ETL operations
```

## Validation Configuration

```env
VALIDATE_BEFORE_INGEST=true      # Run SHACL before loading
SHACL_SHAPES_DIR=docs/ontology/shacl    # Location of SHACL shapes
ABORT_ON_VALIDATION_FAILURE=true # Stop if validation fails
```

## Logging Configuration

```env
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/kgcs.log           # Log file path (optional)
```

## Using Configuration in Code

### Simple Access

```python
from src.config import neo4j_config, etl_config, validation_config

# Get Neo4j credentials
uri = neo4j_config.uri
user = neo4j_config.user
password = neo4j_config.password

# Get ETL settings
batch_size = etl_config.batch_size
parallelism = etl_config.parallelism
```

### Full Configuration Object
```python
from src.config import config

# Access any setting
print(config.neo4j.uri)
print(config.etl.batch_size)
print(config.validation.validate_before_ingest)

# Export configuration (no secrets)
config_dict = config.to_dict()
```

### Validation
```python
from src.config import config

if not config.validate_all():
    raise ValueError("Invalid configuration")
```

## Environment-Specific Configuration

### Local Development
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=password              # Simple password for testing
LOG_LEVEL=DEBUG                      # Verbose logging
VALIDATE_BEFORE_INGEST=true
```

### Testing
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_DATABASE=test_kgcs             # Separate test database
ABORT_ON_VALIDATION_FAILURE=false    # Allow test data violations
LOG_LEVEL=INFO
```

### Production
```env
NEO4J_URI=bolt://neo4j-prod:7687
NEO4J_PASSWORD=<secure-random-password>  # Use secrets manager!
NEO4J_ENCRYPTED=true
LOG_LEVEL=WARNING                    # Less verbose
VALIDATE_BEFORE_INGEST=true
ABORT_ON_VALIDATION_FAILURE=true     # Strict validation
```

## Secrets Management

### For Local Development
1. Create `.env` with your credentials
2. It's gitignored and stays on your machine

### For Production / CI/CD
**Never commit secrets to git.** Instead:

1. **GitHub Actions:** Use repository secrets
   ```yaml
   - name: Run ETL
     env:
       NEO4J_PASSWORD: ${{ secrets.NEO4J_PASSWORD }}
       NEO4J_URI: ${{ secrets.NEO4J_URI }}
     run: python -m src.scripts.ingest_pipeline
   ```

2. **Docker:** Use environment variables
   ```bash
   docker run \
     -e NEO4J_PASSWORD=$NEO4J_PASSWORD \
     -e NEO4J_URI=$NEO4J_URI \
     kgcs:latest
   ```

3. **Kubernetes:** Use secrets
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: neo4j-secrets
   data:
     password: <base64-encoded>
     uri: <base64-encoded>
   ```

## Troubleshooting

### "Missing .env file"
Create it from template:
```bash
cp .env.example .env
```

### "Connection refused"
Check Neo4j is running and URI is correct:
```bash
neo4j status           # Check if Neo4j is running
python -m src.config  # Print configuration
```

### "Authentication failed"
Verify credentials in `.env`:
```bash
# Test with neo4j-cli
cypher-shell -u neo4j -p $NEO4J_PASSWORD -a $NEO4J_URI "MATCH (n) RETURN COUNT(n)"
```

### "Module 'dotenv' not found"
Install python-dotenv (optional):
```bash
pip install python-dotenv
```

## Configuration Files Reference

| File | Purpose | Committed | Contains Secrets |
|------|---------|-----------|------------------|
| `.env.example` | Template for developers | ✓ YES | ✗ NO |
| `.env` | Local configuration | ✗ NO | ✓ YES |
| `src/config.py` | Configuration module | ✓ YES | ✗ NO |
| `requirements.txt` | Python dependencies | ✓ YES | ✗ NO |

## Examples

### Example 1: Basic Neo4j Connection
```python
from src.config import neo4j_config
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    neo4j_config.uri,
    auth=(neo4j_config.user, neo4j_config.password)
)
```

### Example 2: ETL with Configuration
```python
from src.config import etl_config
from src.etl.etl_cpe import CPEtoRDFTransformer

transformer = CPEtoRDFTransformer()
# Use ETL config
batch_size = etl_config.batch_size
parallelism = etl_config.parallelism
```

### Example 3: Conditional Validation
```python
from src.config import validation_config
from src.core.validation import run_validator

if validation_config.validate_before_ingest:
    conforms, report, _ = run_validator(data_file, shapes_graph)
    if not conforms and validation_config.abort_on_failure:
        raise ValueError("Validation failed")
```

## Next Steps

1. [Create `.env` from `.env.example`]
2. [Install python-dotenv](#installation)
3. [Test configuration with `python -m src.config`](#testing-configuration)
4. [Proceed with Neo4j setup and data loading](../PHASE-3-PROGRESS.md)
