# Neo4j Statistics Extraction Guide

## Quick Start

Extract all statistics from the most recently updated database:

```bash
python scripts/extract_neo4j_stats.py
```

**Options:**

- `--output` — Save JSON to specific file (default: `artifacts/neo4j-stats.json`)
- `--db DATABASE` — Use specific database by name (default: auto-detect most recent)
- `--pretty` — Pretty-print JSON output
- `--list-databases` — List available databases and exit

**Examples:**

```bash
# Auto-detect most recently updated database
python scripts/utilities/extract_neo4j_stats.py

# List all available databases
python scripts/utilities/extract_neo4j_stats.py --list-databases

# Extract from specific database with pretty-print
python scripts/utilities/extract_neo4j_stats.py --db neo4j-2026-01-29 --pretty

# Save to custom location
python scripts/utilities/extract_neo4j_stats.py --output /tmp/stats.json
```

## What Gets Extracted

### 1. Node Statistics

- Total nodes by label (Platform, Vulnerability, Technique, etc.)
- Count breakdown for all 13 core entity types

### 2. Relationship Statistics

- Total relationships by type (CAUSED_BY, MITIGATED_BY, DETECTED_BY, etc.)
- Relationship pattern breakdown (source → target by label)

### 3. Causal Chain Analysis

- CVE → CWE links (vulnerabilities to weaknesses)
- CWE → CAPEC links (weaknesses to attack patterns)
- CAPEC → Technique links (attack patterns to ATT&CK)
- CVE → PlatformConfiguration links (affected systems)

### 4. Cross-Standard Linkage

- Technique → Defense links (D3FEND mitigations)
- Technique → Detection links (CAR analytics)
- Technique → Deception links (SHIELD techniques)
- Technique → Engagement links (ENGAGE strategies)

### 5. Data Quality Metrics

- Orphaned nodes (entities with no relationships)
- CVSS version coverage (v2.0, v3.1, v4.0 distribution)
- Platform/PlatformConfiguration breakdown
- Techniques by tactic (coverage analysis)
- CVE → CWE coverage percentage
- Technique → Defense coverage percentage

### 6. Relationship Patterns

- Top 30 relationship patterns by frequency
- Source → Target label combinations
- Useful for understanding graph connectivity

## Example Output

```text
================================================================================
NEO4J KGCS STATISTICS EXTRACTION
================================================================================

Connecting to Neo4j at bolt://localhost:7687...
✅ Connected successfully

Extracting node statistics...
Extracting relationship statistics...
Analyzing causal chain...
...
✅ Statistics extracted successfully

📊 Statistics written to: artifacts/neo4j-stats.json

================================================================================
SUMMARY
================================================================================

Total Nodes: 250,000
Total Relationships: 500,000

Node Breakdown (Top 15):
  Platform: 100,000
  PlatformConfiguration: 80,000
  Vulnerability: 30,000
  Weakness: 12,000
  ...

Causal Chain Analysis:
  cve_to_cwe: 28,500
  cwe_to_capec: 8,200
  capec_to_technique: 520
  cve_to_platform_config: 80,000

Cross-Standard Linkage:
  technique_to_defense: 410
  technique_to_detection: 380
  technique_to_deception: 150
  technique_to_engagement: 50

CVE → CWE Coverage: 28,500/30,000 (95.0%)
Technique → Defense Coverage: 410/520 (78.8%)

CVSS Version Coverage:
  v2.0: 5,000
  v3.1: 28,000
  v4.0: 500
```

## Command Line Options

| Option | Purpose | Default | Example |
| --- | --- | --- | --- |
| `--output` | Output JSON file | `artifacts/neo4j-stats.json` | `--output /tmp/stats.json` |
| `--db` | Target database | Auto-detect most recent | `--db neo4j-2026-01-29` |
| `--pretty` | Pretty-print JSON | False | `--pretty` |
| `--list-databases` | List available DBs | N/A | `--list-databases` |

### Database Auto-Detection

By default, the script automatically selects the most recently updated database:

```bash
# Will auto-detect the most recent database
python scripts/extract_neo4j_stats.py
# Output: "✅ Using database: neo4j-2026-01-29"
```

To see all available databases:

```bash
python scripts/extract_neo4j_stats.py --list-databases
# Output:
#   - neo4j (online)
#   - neo4j-2026-01-28 (online)
#   - neo4j-2026-01-29 (online)
#   - system (online)
```

To use a specific database:

```bash
python scripts/extract_neo4j_stats.py --db neo4j-2026-01-28
```

## Analyzing the Output JSON

The statistics are saved to `artifacts/neo4j-stats.json` with this structure:

```json
{
  "timestamp": "2026-02-03T14:30:00...",
  "database": "neo4j",
  "nodes": {
    "Platform": 100000,
    "Vulnerability": 30000,
    ...
  },
  "relationships": {
    "CAUSED_BY": 28500,
    "MITIGATED_BY": 410,
    ...
  },
  "totals": {
    "nodes": 250000,
    "relationships": 500000
  },
  "causal_chain_analysis": {
    "cve_to_cwe": 28500,
    ...
  },
  "quality_metrics": {
    "orphaned_nodes": { ... },
    "cvss_versions": { ... },
    "cve_cwe_coverage": { ... },
    ...
  }
}
```

## Key Insights to Look For

1. **Causal Chain Completeness**
   - Check `cve_to_cwe`, `cwe_to_capec`, `capec_to_technique` counts
   - Should form a connected chain (CVEs → CWEs → CAPECs → Techniques)

2. **Cross-Standard Coverage**
   - Look at coverage percentages: CVE→CWE, Technique→Defense
   - High percentages = good ontology alignment

3. **Orphaned Nodes**
   - Any orphaned nodes indicate incomplete data
   - Common: orphaned References, orphaned Scores

4. **CVSS Version Distribution**
   - v3.1 should be most common (modern standard)
   - v2.0 declining, v4.0 still limited

5. **Relationship Patterns**
   - Look for unexpected patterns
   - Technique should have PART_OF to Tactic
   - Vulnerability should have AFFECTS to PlatformConfiguration

## Troubleshooting

**Connection Error?**

- Verify Neo4j is running: `neo4j status`
- Check `.env.devel` for correct URI, user, password
- Verify database exists: `python -c "from src.config import neo4j_config; print(neo4j_config.uri)"`

**No nodes/relationships found?**

- Check that ETL data was loaded: `python src/etl/rdf_to_neo4j.py --dry-run`
- Verify Neo4j database is not empty: `MATCH (n) RETURN COUNT(n)`

**Slow extraction?**

- Neo4j might be rebuilding indexes
- Run with `--db` to use a smaller test database
- Check server load: `CALL dbms.virtualFile.list()`

## Integration with CI/CD

The script is designed to be CI-friendly:

```bash
# Extract stats and fail if nodes < 100000
python scripts/extract_neo4j_stats.py || exit 1

# Parse JSON and validate
python -c "
import json
stats = json.load(open('artifacts/neo4j-stats.json'))
nodes = stats['totals']['nodes']
if nodes < 100000:
    print(f'ERROR: Only {nodes} nodes loaded (expected > 100,000)')
    exit(1)
print(f'✅ Graph loaded: {nodes} nodes, {stats[\"totals\"][\"relationships\"]} relationships')
"
```

## Next: Visualizing the Stats

Use the JSON output to create dashboards:

- Plot node/relationship trends over time
- Track coverage metrics (CVE→CWE%, Technique→Defense%)
- Monitor for orphaned nodes (data quality)
- Build reports for stakeholders

See [PROJECT-STATUS-SUMMARY.md](../PROJECT-STATUS-SUMMARY.md) for integration with project milestones.
