# KGCS Documentation

Welcome to the KGCS (Cybersecurity Knowledge Graph) documentation. This directory contains all the information you need to understand, deploy, and maintain the system.

---

## 🎯 Where to Start?

**New to KGCS?** Start here:

1. [**KGCS.md**](KGCS.md) — Executive summary and big picture
2. [**ARCHITECTURE.md**](ARCHITECTURE.md) — System design and 5-phase roadmap
3. [**GLOSSARY.md**](GLOSSARY.md) — Standard definitions and terminology
4. [**PIPELINE_EXECUTION_GUIDE.md**](PIPELINE_EXECUTION_GUIDE.md) — End-to-end pipeline execution

**Want to extend the system?**

- [**EXTENDING.md**](EXTENDING.md) — How to add new standards or features

---

## 📚 Documentation Structure

### Core Architecture (Read These First)

| Document | Purpose |
| --- | --- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, 5-phase implementation roadmap, design decisions |
| [KGCS.md](KGCS.md) | Executive summary, core principles, why KGCS matters |
| [GLOSSARY.md](GLOSSARY.md) | Definitions of standards, ontology concepts, and relationships |
| [EXTENDING.md](EXTENDING.md) | How to add new standards or extend the system |

### 📋 Operations & Deployment

Need to deploy, run, or maintain the system?

| Document | Purpose |
| --- | --- |
| [operations/DEPLOYMENT.md](operations/DEPLOYMENT.md) | Production Neo4j setup and deployment procedures |
| [operations/DAILY-DOWNLOAD-PIPELINE.md](operations/DAILY-DOWNLOAD-PIPELINE.md) | Automating daily data downloads from all standards |
| [operations/CLEANUP-WORKSPACE.md](operations/CLEANUP-WORKSPACE.md) | Cleaning up temporary files and caches |
| [operations/NEO4J-LOAD-SUMMARY.md](operations/NEO4J-LOAD-SUMMARY.md) | Latest Neo4j statistics and load analysis |
| [operations/NEO4J-STATS.md](operations/NEO4J-STATS.md) | Guide to extracting Neo4j statistics |
| [PIPELINE_EXECUTION_GUIDE.md](PIPELINE_EXECUTION_GUIDE.md) | Full pipeline execution guide (download → ETL → load) |

**Quick Links:**

- **Deploy to production?** → [DEPLOYMENT.md](operations/DEPLOYMENT.md)
- **Set up automated downloads?** → [DAILY-DOWNLOAD-PIPELINE.md](operations/DAILY-DOWNLOAD-PIPELINE.md)
- **Check Neo4j statistics?** → [NEO4J-LOAD-SUMMARY.md](operations/NEO4J-LOAD-SUMMARY.md)
- **Need to clean up?** → [CLEANUP-WORKSPACE.md](operations/CLEANUP-WORKSPACE.md)
- **Run the full pipeline?** → [PIPELINE_EXECUTION_GUIDE.md](PIPELINE_EXECUTION_GUIDE.md)

### 🔬 Research & Enhancement Reports

Historical reports and analysis of Phase 3 enhancements.

| Document | Purpose |
| --- | --- |
| [research/CAPEC-ENHANCEMENT-FINAL-REPORT.md](research/CAPEC-ENHANCEMENT-FINAL-REPORT.md) | CAPEC 8.5x improvement: detailed analysis and results |
| [research/PHASE3-ENHANCEMENT-COMPLETION.md](research/PHASE3-ENHANCEMENT-COMPLETION.md) | Phase 3 enhancement work completion summary |
| [research/PHASE3-STATUS-SUMMARY.md](research/PHASE3-STATUS-SUMMARY.md) | Phase 3 final status and metrics |
| [research/CAPEC_MAPPING_DISCOVERY.md](research/CAPEC_MAPPING_DISCOVERY.md) | Discovery process for CAPEC XML mappings |
| [research/PIPELINE_REGENERATION_SUMMARY.md](research/PIPELINE_REGENERATION_SUMMARY.md) | Pipeline regeneration with enhanced CAPEC |

### 🏛️ Formal Specifications

Core ontology and validation framework specifications.

| Directory | Purpose |
| --- | --- |
| [ontology/](ontology/) | OWL ontologies, SHACL shapes, and formal definitions |

---

## 🔍 Find What You Need

### By Role

#### System Architect or Designer

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [KGCS.md](KGCS.md)
- [GLOSSARY.md](GLOSSARY.md)

#### DevOps / System Administrator

- [operations/DEPLOYMENT.md](operations/DEPLOYMENT.md)
- [operations/DAILY-DOWNLOAD-PIPELINE.md](operations/DAILY-DOWNLOAD-PIPELINE.md)
- [operations/NEO4J-LOAD-SUMMARY.md](operations/NEO4J-LOAD-SUMMARY.md)

#### Developer / Data Engineer

- [EXTENDING.md](EXTENDING.md)
- [ontology/](ontology/)
- [operations/NEO4J-STATS.md](operations/NEO4J-STATS.md)
- [PIPELINE_EXECUTION_GUIDE.md](PIPELINE_EXECUTION_GUIDE.md)

#### Researcher / Analyst

- [research/](research/)
- [ARCHITECTURE.md](ARCHITECTURE.md)

### By Topic

#### Understanding the System

- Core principles: [KGCS.md](KGCS.md)
- Architecture & design: [ARCHITECTURE.md](ARCHITECTURE.md)
- Definitions & terms: [GLOSSARY.md](GLOSSARY.md)

#### Adding New Standards

- [EXTENDING.md](EXTENDING.md)
- [ontology/](ontology/)

#### Running the System

- Deployment: [operations/DEPLOYMENT.md](operations/DEPLOYMENT.md)
- Daily automation: [operations/DAILY-DOWNLOAD-PIPELINE.md](operations/DAILY-DOWNLOAD-PIPELINE.md)
- Statistics: [operations/NEO4J-LOAD-SUMMARY.md](operations/NEO4J-LOAD-SUMMARY.md)

#### Understanding Phase 3

- [research/CAPEC-ENHANCEMENT-FINAL-REPORT.md](research/CAPEC-ENHANCEMENT-FINAL-REPORT.md)
- [research/PHASE3-ENHANCEMENT-COMPLETION.md](research/PHASE3-ENHANCEMENT-COMPLETION.md)

---

## 📊 Key Metrics

- **11 OWL Ontologies** — Core system specifications
- **25+ SHACL Shapes** — Validation rules
- **2.5M Neo4j Nodes** — Knowledge graph content
- **26M Relationships** — Cross-standard links
- **10 Data Standards** — CPE, CVE, CVSS, CWE, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE

---

## 🚀 Quick Commands

```bash
# View latest Neo4j statistics
python scripts/utilities/extract_neo4j_stats.py --pretty

# Deploy to production
# See: docs/operations/DEPLOYMENT.md

# Set up automated downloads
# See: docs/operations/DAILY-DOWNLOAD-PIPELINE.md

# Run the complete ETL pipeline
python scripts/run_all_etl.py

# Validate all standards
python scripts/validation/validate_all_standards.py
```

---

## 📖 Related Documentation

See [REPOSITORY-ORGANIZATION-SUMMARY.md](../REPOSITORY-ORGANIZATION-SUMMARY.md) for overall project structure.

See [PROJECT-STATUS-SUMMARY.md](../PROJECT-STATUS-SUMMARY.md) for current project status and roadmap.

---

## 💡 Tips

- **Use Ctrl+F** to search within this README
- **Check the operations folder** for deployment and maintenance guides
- **Review research folder** for historical context and enhancement details
- **Reference GLOSSARY.md** if you encounter unfamiliar terms
- **Start with KGCS.md** if you're new to the project

---

**Last Updated:** February 10, 2026  
**Status:** ✅ Complete documentation structure
