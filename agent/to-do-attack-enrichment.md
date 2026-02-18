## To-Do: ATT&CK Enrichment

Here is an analysis of your to-do-attack.md versus the official ATT&CK-STIX schema, with recommendations for congruence and extension placement:

### 1. Technique/SubTechnique Modeling

- **Current (to-do-attack.md):** Separate classes for Technique and SubTechnique.
- **Official Schema:** Both are `attack-pattern` objects, with subtechniques distinguished by `x_mitre_is_subtechnique: true` and a parent reference.
- **Recommendation:** Refactor to a single `Technique` class with an `x_mitre_is_subtechnique` property and a `subtechnique_of` relationship. This matches the schema and simplifies the ontology.

### 2. Group, Software, Asset, DataSource, DataComponent

- **Current:** Not present or only as properties, not as node types.
- **Official Schema:**
  - Group: `intrusion-set`
  - Software: `malware` and `tool`
  - Asset: `x-mitre-asset`
  - DataSource/DataComponent: `x-mitre-data-source`, `x-mitre-data-component`
- **Recommendation:**
  - Define `Group`, `Software`, `Malware`, `Tool`, `Asset`, `DataSource`, and `DataComponent` as classes.
  - These should be defined in a threat extension (not the immutable core), as they are not part of the minimal core but are essential for full ATT&CK coverage and reasoning.
  - Relationships like `uses`, `employs`, `targets`, etc., should also be defined in the extension.

### 3. Properties and Relationships

- **Current:** Many STIX fields (aliases, labels, kill_chain_phases, external_references, object_marking_refs, etc.) are not mapped.
- **Official Schema:** All these are present and important for traceability and standards alignment.
- **Recommendation:**
  - Map all required and recommended STIX properties as datatype or object properties.
  - Multi-valued fields (aliases, labels, etc.) should be repeated triples.
  - References (created_by_ref, external_references, object_marking_refs) should create/link referenced nodes.
  - Update SHACL shapes to validate these properties.

### 4. Placement in Threat Extension

- **Classes to define in threat extension:**
  - `Group` (maps to `intrusion-set`)
  - `Software` (abstract, with subclasses `Malware` and `Tool`)
  - `Asset`
  - `DataSource`
  - `DataComponent`
- **Relationships to define in threat extension:**
  - `uses` (Group/Software → Technique)
  - `employs` (Group → Tool)
  - `implements` (Tool → Technique)
  - `targets` (Technique → Asset)
  - `detects` (DataComponent → Technique)
  - `associatedGroup`, `hasMitigation`, etc.

### 5. Other Incongruences

- **Subclassing:** Avoid subclassing for subtechniques; use the property-based approach.
- **Deprecated fields:** Mark deprecated fields as such and plan for their removal in future versions.
- **SHACL:** Extend SHACL to cover all new properties and relationships.

---

## 6. Mapping All Relevant STIX Properties and Relationships

The following STIX properties and relationships should be mapped to the ontology and ETL:

### Core Properties (for all ATT&CK objects)

- `id` → `sec:attackId` (IRI/identifier)
- `type` → `rdf:type` (e.g., Technique, Group, Software, etc.)
- `spec_version` → `sec:specVersion` (datatype property)
- `created` → `sec:created` (xsd:dateTime)
- `modified` → `sec:modified` (xsd:dateTime)
- `created_by_ref` → `sec:createdBy` (object property to Identity node)
- `labels` → `sec:labels` (multi-valued string)
- `name` → `rdfs:label` (string)
- `description` → `sec:description` (string)
- `aliases` → `sec:aliases` (multi-valued string)
- `external_references` → `sec:externalReference` (object property to Reference node)
- `object_marking_refs` → `sec:objectMarking` (object property to Marking node)
- `kill_chain_phases` → `sec:killChainPhase` (multi-valued string or node)
- `x_mitre_domains` → `sec:domains` (multi-valued string)
- `x_mitre_attack_spec_version` → `sec:attackSpecVersion` (string)
- `x_mitre_version` → `sec:attackVersion` (string)
- `x_mitre_deprecated` → `sec:deprecated` (boolean)
- `x_mitre_contributors` → `sec:contributors` (multi-valued string)

### Technique/Subtechnique Specific

- `x_mitre_is_subtechnique` → `sec:isSubtechnique` (boolean)
- `x_mitre_platforms` → `sec:platforms` (multi-valued string)
- `x_mitre_detection` → `sec:detection` (string, deprecated)
- `x_mitre_data_sources` → `sec:dataSources` (multi-valued string, deprecated)
- `x_mitre_permissions_required` → `sec:permissionsRequired` (multi-valued string, deprecated)
- `x_mitre_effective_permissions` → `sec:effectivePermissions` (multi-valued string, deprecated)
- `x_mitre_network_requirements` → `sec:networkRequirements` (string)
- `subtechnique_of` → `sec:subtechnique_of` (object property to parent Technique)
- `sec:belongs_to` (object property to Tactic)

### Group/Software/Asset/DataSource/DataComponent

- `intrusion-set` → `sec:Group` (class)
- `malware`/`tool` → `sec:Malware`/`sec:Tool` (subclasses of Software)
- `x-mitre-asset` → `sec:Asset` (class)
- `x-mitre-data-source` → `sec:DataSource` (class)
- `x-mitre-data-component` → `sec:DataComponent` (class)

### Relationships

- `uses` (Group/Software → Technique/Software)
- `employs` (Group → Tool)
- `implements` (Tool → Technique)
- `targets` (Technique → Asset)
- `detects` (DataComponent → Technique)
- `associatedGroup`, `hasMitigation`, etc.

All multi-valued fields should be mapped as repeated triples. References should create/link referenced nodes.

---

## 7. Example: CAPEC Relationship via external_references

When processing an `attack-pattern` object from ATT&CK raw data, the `external_references` array may include references to other standards, such as CAPEC. For example:

```json
{
  "type": "attack-pattern",
  ...
  "external_references": [
    {
      "source_name": "mitre-attack",
      "url": "https://attack.mitre.org/techniques/T1148",
      "external_id": "T1148"
    },
    {
      "source_name": "capec",
      "url": "https://capec.mitre.org/data/definitions/13.html",
      "external_id": "CAPEC-13"
    }
  ],
  ...
}
```

### Mapping Guidance

- For each `external_references` entry:
  - If `source_name` is `capec` and `external_id` matches the CAPEC pattern, create a relationship from the Technique node to the corresponding CAPEC node (e.g., `sec:derived_from` or `sec:capecReference`).
  - The CAPEC node should be represented in the graph with its canonical identifier (e.g., `capec:CAPEC-13`).
  - The relationship must be traceable to the original STIX data (include provenance if possible).
- Other `external_references` (e.g., mitre-attack) should be mapped as reference nodes or literals as appropriate.

### Example RDF (Turtle)

```turtle
sec:attack-pattern--086952c4-5b90-4185-b573-02bad8e11953
  a sec:Technique ;
  rdfs:label "HISTCONTROL" ;
  sec:attackId "attack-pattern--086952c4-5b90-4185-b573-02bad8e11953" ;
  sec:capecReference capec:CAPEC-13 ;
  ... .

capec:CAPEC-13
  a capec:Attack_Pattern ;
  rdfs:label "CAPEC-13" .
```

### Patch Plan Update

- **Ontology:**
  - Add `sec:capecReference` (or `sec:derived_from`) as an object property from Technique to CAPEC Attack_Pattern.
- **ETL:**
  - Update ETL logic to parse `external_references` and emit the appropriate triple for CAPEC references.
  - Ensure CAPEC nodes are created or linked as needed.
- **SHACL:**
  - Add shape to validate that Techniques referencing CAPEC have a valid `sec:capecReference` property.
- **Documentation:**
  - Document this mapping pattern and rationale in the ontology/ETL docs.

---

## 8. Concrete Patch Plan for Ontology and Extension Files

### 8.1. Core Ontology (if needed)

- Remove separate SubTechnique class; unify as Technique with `sec:isSubtechnique` property.
- Ensure all core properties (id, type, created, modified, etc.) are present.

### 8.2. Threat Extension Ontology

- Define new classes: Group, Software, Malware, Tool, Asset, DataSource, DataComponent.
- Define new object properties: uses, employs, implements, targets, detects, associatedGroup, hasMitigation, etc.
- Add all relevant datatype/object properties for STIX fields (see above mapping).
- Ensure all relationships are traceable to source data (no fabricated edges).

### 8.3. SHACL Shapes

- Update shapes to validate new properties and relationships (including multi-valued and reference fields).
- Add shapes for new classes in the threat extension.
- Mark deprecated fields as optional or to be removed in future.

### 8.4. ETL Pipeline

- Refactor ETL logic to emit unified Technique nodes with `sec:isSubtechnique` property.
- Extend ETL to emit all mapped STIX properties and relationships.
- Ensure ETL creates/link referenced nodes for object properties (e.g., created_by_ref, external_references).
- Add/extend tests for new fields and relationships.

### 8.5. Documentation

- Update ontology and ETL documentation to reflect new modeling approach and mappings.
- Document all changes, rationale, and any edge cases.
