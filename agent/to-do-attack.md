# ATT&CK Data/Ontology/ETL Gap Analysis

Here’s a summary of the ATT&CK data/ontology/ETL situation and next steps for gap analysis:

---

**1. Raw Data (enterprise-attack.json):**

- Contains rich STIX 2.1 objects: x-mitre-matrix, x-mitre-tactic, attack-pattern, course-of-action, group, software, marking, etc.
- Each object has many attributes: id, type, created, modified, external_references, platforms, domains, kill_chain_phases, etc.
- Relationships are often implicit via references (e.g., tactic_refs, kill_chain_phases, object_marking_refs).

**2. Current Ontology (attack-ontology-v1.0.md & SHACL):**

- Models core classes: Tactic, Technique, SubTechnique, Group, Software, DataSource, DataComponent, Asset.
- Main relationships: contains, subtechnique_of, uses, detects, targets.
- SHACL shapes enforce basic structure (e.g., Technique must have attackTechniqueId, label, belongs_to Tactic).

**3. ETL (etl_attack.py):**

- Transforms STIX JSON to RDF, mapping only a subset of fields (mainly id, name, description, tactic-technique links).
- Focuses on Tactic, Technique, SubTechnique, Group, Software.
- Likely omits: kill_chain_phases, platforms, domains, marking, external references, detection, mitigations, and other STIX object types.

**4. External Ontology (data/attack/schemas/ontology.ttl):**

- More detailed: includes properties like accomplishesTactic, associatedGroup, hasAdversaryGroup, hasMitigation, hasPlatform, hasDataSource, etc.
- Models more relationships and attributes than current KGCS ontology.

**5. STIX Schema (attack-pattern.json):**

- Defines all possible fields for attack-pattern objects, including aliases, kill_chain_phases, external references, etc.

---

**Gaps & Opportunities:**

- **Missing in KGCS graph:** Many STIX fields (aliases, platforms, domains, kill_chain_phases, marking, external references, detection, mitigations, etc.) are not mapped or represented in the ontology or ETL output.
- **Ontology enrichment:** The external ontology (ontology.ttl) models more relationships and attributes—these can be selectively adopted to enrich the KGCS ontology.
- **ETL enhancement:** The ETL should be extended to extract and emit all relevant fields and relationships, not just the core tactic/technique/group/software structure.
- **SHACL/validation:** SHACL shapes should be updated to validate the richer structure if new fields/relationships are added.

---

**Next Steps:**

1. List all fields and relationships present in the raw STIX data but missing from the current ontology/ETL.
2. Propose ontology/ETL/SHACL updates to cover these gaps, referencing the external ontology for property/relationship ideas.
3. Prioritize which attributes/relationships are most valuable for reasoning, RAG, or downstream applications.
