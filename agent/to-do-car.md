# CAR Ontology & ETL Gap Analysis

**Branch:** feature/car-ontology-enrichment
**Last Updated:** February 17, 2026

---

## 1. Raw Data Review

- List all fields, relationships, and attributes present in CAR raw files (YAML, JSON, etc.)
- Identify entities (Analytic, Technique, DataSource, Sensor, Datamodel, etc.) and their properties
- Reference schemas/analytic_schema.yaml, datamodel_schema.yaml, sensor_schema.yaml for authoritative field definitions

## 2. Current Ontology Review

- Summarize classes, properties, and relationships in docs/ontology/owl/car-ontology-v1.0.owl and car-ontology-v1.0.md
- Note which fields/relationships are modeled and which are missing

### Ontology Coverage (from car-ontology-v1.0.owl and CAR schemas)

- **Core Classes:**
  - `car:Analytic` (root for detection analytics)
    - Subclasses: `Detection`, `Correlation`, `Enrichment`, `Alerting`, `Hunting`, `Reporting`
  - `car:Technique`
  - `car:DataSource`
  - `car:Sensor`
  - `car:Datamodel`
  - `car:StakeholderImpact`
- **Key Datatype Properties (from schemas):**
  - Analytic: title, submission_date, update_date, information_domain, platforms, subtypes, analytic_types, contributors, id, description, coverage, implementations, unit_tests, true_positives, data_model_references, references, d3fend_mappings
  - Datamodel: name, description, actions, fields, coverage
  - Sensor: sensor_name, sensor_version, sensor_developer, sensor_url, sensor_description, data_model_coverage, analytic_coverage, mappings, other_coverage
- **Key Object Properties:**
  - `car:detects` / `car:detected_by` (links Analytic to sec:Technique)
  - `car:usesDataSource` / `car:dataSource_for_analytic`
  - `car:achieves` / `car:achieved_by` (links Analytic to StakeholderImpact)
  - `car:applicableInContext` / `car:context_for_analytic`
  - `car:hasImpact` / `car:impact_of`
  - `car:complementedBy` (symmetric, between Analytics)
  - `car:requiresCoordination` / `car:coordinated_with`
  - `car:affects` / `car:affected_by_analytic` (links to sec:AttackPattern)
  - `car:hasSensor` / `car:hasDatamodel`
- **Constraints (SHACL-informative):**
  - Analytics must have: carId, name, description, analyticType, timeframe, operationalLevel, effectivenessMetric, and at least one detects or affects relationship.
  - Techniques, DataSources, Sensors, Datamodels, and StakeholderImpact have required fields as well.
- **Example Relationships:**
  - Analytics can detect techniques, use data sources, achieve impacts, be applicable in contexts, complement or coordinate with other analytics, reference sensors and datamodels.

### Gaps vs. ETL

- Many schema fields (e.g., coverage, implementations, unit_tests, true_positives, d3fend_mappings, sensor mappings, datamodel actions/fields) are not mapped in the ETL.
- Object properties like achieves, applicableInContext, hasImpact, complementedBy, requiresCoordination, affects, usesDataSource, hasSensor, hasDatamodel are not present in the ETL output.
- Subclass structure (e.g., Detection, Correlation) is not reflected in the ETL.

## 3. ETL & Output Review

- Review src/etl/etl_car.py and sample TTL outputs
- Identify which raw fields from schemas/analytic_schema.yaml, datamodel_schema.yaml, sensor_schema.yaml are mapped, which are omitted

### Prioritized ETL/Enrichment Tasks

1. **Map all required CAR ontology and schema properties:**
   - Add support for coverage, implementations, unit_tests, true_positives, d3fend_mappings, sensor mappings, datamodel actions/fields, and all required fields for Analytic, Technique, DataSource, Sensor, Datamodel, and StakeholderImpact.
2. **Implement subclass structure:**
   - Reflect subclasses (e.g., Detection, Correlation, etc.) in ETL output, using correct RDF types.
3. **Add object property relationships:**
   - Support achieves, applicableInContext, hasImpact, complementedBy, requiresCoordination, affects, usesDataSource, hasSensor, hasDatamodel as per ontology and schemas.
   - Ensure relationships are traceable to source data and not fabricated.
4. **Enforce SHACL constraints:**
   - Validate ETL output against SHACL shapes to ensure all mandatory fields and relationships are present.
5. **Extend ETL for unmapped raw fields:**
   - Review CAR raw data and schemas for any fields or relationships not currently mapped; extend ETL to cover them.
6. **Document all changes and gaps:**
   - Update this file and ETL documentation with all improvements, gaps, and reasoning value.
7. **Prioritize by reasoning and RAG value:**
   - Focus on properties and relationships that improve downstream reasoning, RAG safety, and operational traceability.

## 4. External Ontology Comparison

- Review any external CAR ontologies in schemas folder
- List additional properties/relationships that could enrich KGCS

## 5. Gap Table

| Raw Field/Relationship | Ontology | ETL | TTL Output | External Ontology | Gap/Notes |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## 6. Recommendations

- Propose ontology/ETL/SHACL updates to cover gaps
- Prioritize by reasoning value, RAG, downstream use

## 7. Next Steps

- Plan implementation tasks for branch
- Update this file as analysis progresses
