# Extending KGCS: Adding New Standards

**Purpose:** Guide for adding new security standards to KGCS.

---

## When to Add to Core vs. Extension

### Add to Core If

- Standard is authoritative (e.g., NVD, MITRE)
- Provides 1:1 mapping to official schema
- Fits into causal chain (CPE → CVE → ... → Defense)
- Will be used by multiple applications
- Rarely changes (frozen after Phase 1)

**Examples:** CPE, CVE, CWE, CAPEC, ATT&CK, D3FEND, CAR, SHIELD, ENGAGE

### Add to Extension If

- Data is contextual, temporal, or subjective
- Organization-specific or assessment-based
- Requires frequent updates
- References core concepts

**Examples:** Incident, Risk, ThreatActor, RiskAssessment

---

## Adding a Core Standard

### Step 1: Define the Ontology

Create `docs/ontology/owl/<standard>-ontology.owl`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:owl="http://www.w3.org/2002/07/owl#"
    xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
    xmlns:sec="https://example.org/sec/">
    
    <!-- Import core -->
    <owl:imports rdf:resource="https://example.org/sec/core-ontology-v1.0.owl"/>
    
    <!-- Define classes -->
    <owl:Class rdf:about="https://example.org/sec/YourEntity">
        <rdfs:label>Your Entity</rdfs:label>
        <rdfs:comment>Definition and purpose</rdfs:comment>
    </owl:Class>
    
    <!-- Define properties -->
    <owl:DatatypeProperty rdf:about="https://example.org/sec/yourProperty">
        <rdfs:domain rdf:resource="https://example.org/sec/YourEntity"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
    </owl:DatatypeProperty>
    
    <!-- Define relationships -->
    <owl:ObjectProperty rdf:about="https://example.org/sec/relatesTo">
        <rdfs:domain rdf:resource="https://example.org/sec/YourEntity"/>
        <rdfs:range rdf:resource="https://example.org/sec/OtherEntity"/>
    </owl:ObjectProperty>
    
</rdf:RDF>
```

### Step 2: Write Human-Readable Spec

Create `docs/ontology/<standard>-ontology-v1.0.md`:

```markdown
# [Standard] Ontology v1.0

## Overview
- **Source:** [Official spec URL]
- **Version:** [Latest version]
- **Last Updated:** [Date]

## Core Entities
- **Class:** [Entity] ([Definition])
  - **Properties:** [property1], [property2], ...
  - **Example:** [ID: description]

## Relationships
- **Class A** --[edge]--> **Class B**
  - **Semantics:** [What this relationship means]

## Examples
[Real-world instances]
```

### Step 3: Create SHACL Shapes

Create `docs/ontology/shacl/<standard>-shapes.ttl`:

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#>.
@prefix sec: <https://example.org/sec/>.

# Shape for YourEntity
sec:YourEntityShape
    a sh:NodeShape;
    sh:targetClass sec:YourEntity;
    sh:property [
        sh:path sec:yourProperty;
        sh:minCount 1;
        sh:maxCount 1;
        sh:datatype xsd:string;
    ].
```

### Step 4: Create Test Samples

Create positive and negative examples:

- `data/shacl-samples/<standard>-good.ttl` — Valid RDF
- `data/shacl-samples/<standard>-bad.ttl` — Invalid RDF (missing required properties, wrong types)

### Step 5: Create ETL Transformer

Create `src/etl/etl_<standard>.py`:

```python
from rdflib import Graph, Namespace, URIRef, Literal

class XyztoRDFTransformer:
    def __init__(self):
        self.graph = Graph()
        self.ns = Namespace("https://example.org/sec/")
    
    def transform(self, json_data: dict) -> Graph:
        """
        Transform [Standard] JSON to RDF.
        
        Input: JSON from official source (API/download)
        Output: RDF Graph conforming to [standard]-shapes.ttl
        """
        for item in json_data.get("items", []):
            self._add_entity(item)
        return self.graph
    
    def _add_entity(self, item: dict):
        """Add an entity and its properties to graph."""
        entity_id = item.get("id")
        subj = self.ns[entity_id]
        
        # Type
        self.graph.add((subj, RDF.type, self.ns.YourEntity))
        
        # Properties
        self.graph.add((subj, self.ns.yourProperty, Literal(item.get("name"))))
        
        # Relationships
        for related_id in item.get("related", []):
            self.graph.add((subj, self.ns.relatesTo, self.ns[related_id]))

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True)
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    
    # Load JSON
    import json
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    # Transform
    transformer = XyztoRDFTransformer()
    graph = transformer.transform(data)
    
    # Validate
    if args.validate:
        from src.core.validation import run_validator, load_graph
        shapes = load_graph("docs/ontology/shacl/<standard>-shapes.ttl")
        conforms, _, _ = run_validator(args.output, shapes, "artifacts")
        print("✓ PASS" if conforms else "✗ FAIL")
    
    # Save
    graph.serialize(destination=args.output, format="turtle")
    print(f"Saved {args.output}")

if __name__ == "__main__":
    main()
```

### Step 6: Create Unit Tests

Create `tests/test_<standard>_integration.py`:

```python
import json
import pytest
from src.etl.etl_<standard> import XyztoRDFTransformer
from src.core.validation import run_validator, load_graph

def test_<standard>_etl():
    """Test [Standard] ETL transformer."""
    # Load sample
    with open("data/<standard>/samples/sample_<standard>.json", "r") as f:
        data = json.load(f)
    
    # Transform
    transformer = XyztoRDFTransformer()
    graph = transformer.transform(data)
    
    # Assertions
    assert len(graph) > 0
    assert graph.query("SELECT ?s WHERE { ?s a ?YourEntity }")
```

### Step 7: Update CI/CD

Add to `.github/workflows/shacl-validation.yml`:

```yaml
- name: Validate [Standard]
  run: |
    python scripts/validate_shacl_stream.py \
      --data data/<standard>/samples/sample_<standard>.json \
      --shapes docs/ontology/shacl/<standard>-shapes.ttl
```

### Step 8: Update Documentation

1. Add to [GLOSSARY.md](GLOSSARY.md) — Standard definition + classes + relationships
2. Add to [ARCHITECTURE.md](ARCHITECTURE.md) — Which phase, dependencies
3. Update [GOVERNANCE.md](ontology/GOVERNANCE.md) — Versioning policy, rollback procedure

---

## Adding an Extension

### Step 1: Define the Extension Ontology

Create `docs/ontology/extensions/<extension>-extension.owl`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:owl="http://www.w3.org/2002/07/owl#"
         xmlns:ext="https://example.org/ext/">
    
    <!-- Import core ONLY (one-way) -->
    <owl:imports rdf:resource="https://example.org/sec/core-ontology-v1.0.owl"/>
    
    <!-- Define extension classes -->
    <owl:Class rdf:about="https://example.org/ext/YourContextualEntity">
        <rdfs:label>Contextual Entity</rdfs:label>
        <rdfs:comment>References core, adds context/subjectivity</rdfs:comment>
    </owl:Class>
    
    <!-- Reference core classes (don't redefine) -->
    <owl:ObjectProperty rdf:about="https://example.org/ext/assesses">
        <rdfs:domain rdf:resource="https://example.org/ext/YourContextualEntity"/>
        <rdfs:range rdf:resource="https://example.org/sec/CVE"/>
    </owl:ObjectProperty>
    
</rdf:RDF>
```

### Step 2: Create SHACL Shapes

`docs/ontology/shacl/<extension>-extension-shapes.ttl`

### Step 3: Create Extension Spec

`docs/ontology/<extension>-ontology-extension-v1.0.md`

### Step 4: Implement Python Module

`src/extensions/<extension>.py` — Load extension data independently

### Step 5: **Never Modify Core**

- Extension classes reference core, not vice versa
- Never add properties to core classes
- Never remove from core
- Never alter core relationships

---

## Versioning Policy

### Core Standards

- Versions frozen after Phase 1 release
- Changes require new version (v2.0, v3.0)
- Old versions remain available (no overwrites)
- Deprecation period: announce changes 1–3 months before cutover

### CVSS Special Case

- v2.0, v3.1, v4.0 exist as separate entities (never merged)
- Each CVE may have multiple CVSS versions
- New versions added incrementally

### Extensions

- Can change more frequently (Phase 4+)
- Still versioned (v1.0, v1.1, v2.0)
- Backward-compatible updates preferred

---

## Checklist for Adding a Standard

- [ ] OWL ontology defined (`docs/ontology/owl/`)
- [ ] Human-readable spec written (`docs/ontology/*-ontology-v1.0.md`)
- [ ] SHACL shapes created (`docs/ontology/shacl/*-shapes.ttl`)
- [ ] Positive + negative test samples provided
- [ ] ETL transformer implemented (`src/etl/etl_*.py`)
- [ ] Unit tests written (`tests/test_*_integration.py`)
- [ ] CI/CD updated (`.github/workflows/`)
- [ ] Documentation updated (GLOSSARY, ARCHITECTURE, GOVERNANCE)
- [ ] PR reviewed for:
  - No circular imports
  - Causal chain maintained
  - Explicit provenance (all edges traceable)
  - 1:1 standards alignment verified

---

## References

- [ARCHITECTURE.md](ARCHITECTURE.md) — Phases and dependencies
- [GLOSSARY.md](GLOSSARY.md) — Existing standards + relationships
- [copilot-instructions.md](../.github/copilot-instructions.md) — Development rules
- Example transformers: `src/etl/etl_cpe.py`, `src/etl/etl_cve.py`
