# KGCS – Cybersecurity Knowledge Graph

**Version:** 1.0  
**Date:** January 2026  

---

## 📌 Overview

KGCS (Cybersecurity Knowledge Graph) is a frozen, standards‑backed ontology that unifies nine MITRE security taxonomies (CVE, CWE, CPE, CVSS, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE).  
It provides a single source of truth for AI systems to reason about vulnerabilities, attacks, defenses, and threat intelligence without hallucination.

---

## 🏗️ Architecture

```
┌───────────────────────┐
│  Extension Layer (L4)  │  (Incident, Risk, ThreatActor)
├───────────────────────┤
│  Core Ontology (L3)    │  (CPE → CVE → CWE → CAPEC → ATT&CK → D3FEND/CAR/SHIELD/ENGAGE)
├───────────────────────┤
│  Modular Ontologies    │  (one OWL file per standard)
├───────────────────────┤
│  External Standards    │  (NVD, MITRE)
└───────────────────────┘
```

* **Core** is immutable and 1:1 mapped to official JSON/STIX schemas.  
* **Extensions** add temporal, contextual, or subjective data without polluting the core.

---

## 🔑 Core Invariants

| Invariant | Description |
|-----------|-------------|
| Authoritative alignment | Every class/property maps to a stable ID in NVD or MITRE. |
| Explicit provenance | Every edge is traceable to a source field. |
| No invented semantics | The ontology is a lens, not a replacement for the standards. |
| Extensions never modify core | Incident, Risk, ThreatActor layers reference core only. |

---

## 🚀 Getting Started

1. **Clone the repo**  
   ```bash
   git clone https://github.com/yourorg/kgcs.git
   cd kgcs
   ```

2. **Load data**  
   * Download NVD and MITRE JSON/STIX files into data.  
   * Run the ingestion script (Python/Neo4j or RDF).  

3. **Query the graph**  
   * Use Neo4j Cypher or SPARQL.  
   * Example:  
     ```cypher
     MATCH (cve:Vulnerability {cveId:'CVE-2025-1234'})
     MATCH (cve)-[:caused_by]->(cwe:CWE)
     RETURN cve, cwe
     ```

4. **Integrate with RAG**  
   * Use the pre‑approved traversal templates in rag.  
   * Ensure LLM queries follow a template; otherwise reject.

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| KGCS.md | Executive summary & architecture |
| core-ontology-v1.0.md | Core class & edge definitions |
| RAG-travesal-templates.md | Safe traversal contracts |
| incident-ontology-extension-v1.0.md | Incident extension spec |
| risk-ontology-extension-v1.0.md | Risk extension spec |
| threatactor-ontology-extension-v1.0.md | Threat‑actor extension spec |

---

## 📦 Extensions

* **Incident** – Observed techniques, detections, evidence.  
* **Risk** – Assessments, scenarios, decisions.  
* **ThreatActor** – Attribution claims, capabilities, tools.

Each extension lives in its own OWL file and imports the core ontology.

---

## 📈 Future Work

* Add new standards (e.g., NIST SP 800‑53).  
* SHACL validation: canonical shapes and validator CLI implemented; CI & ETL integration pending.  
* Build a UI for visualizing traversal paths.  
* Integrate with an LLM for explainable answers.

---

## 🤝 Contributing

Pull requests are welcome. Please follow the style guidelines in ontology and keep the core immutable.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---