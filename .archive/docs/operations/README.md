# Operations Guides

Quick reference for running, deploying, and maintaining KGCS.

---

## 📋 Operational Procedures

| Document | Purpose |
| --- | --- |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production Neo4j setup and deployment |
| [DAILY-DOWNLOAD-PIPELINE.md](DAILY-DOWNLOAD-PIPELINE.md) | Automating daily data downloads |
| [CLEANUP-WORKSPACE.md](CLEANUP-WORKSPACE.md) | Cleaning temporary files |
| [NEO4J-LOAD-SUMMARY.md](NEO4J-LOAD-SUMMARY.md) | Latest statistics and analysis |
| [NEO4J-STATS.md](NEO4J-STATS.md) | Statistics extraction guide |

---

## 🚀 Quick Start

**Check Neo4j status:**
```bash
python scripts/utilities/extract_neo4j_stats.py --pretty
```

**Deploy to production:**
See [DEPLOYMENT.md](DEPLOYMENT.md)

**Set up automated downloads:**
See [DAILY-DOWNLOAD-PIPELINE.md](DAILY-DOWNLOAD-PIPELINE.md)

**Clean up workspace:**
See [CLEANUP-WORKSPACE.md](CLEANUP-WORKSPACE.md)

---

**For full documentation:** See [../README.md](../README.md)
