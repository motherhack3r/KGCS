# Verification Scripts

**Purpose:** Interactive tools for visual graph inspection and debugging  
**Approach:** Human-readable output of causal chains and relationships  
**Exit Code:** Always 0 (informational, not CI/CD gates)

---

## Script Files

- `verify_causal_chain.py` — Display vulnerability causality chain
  - Shows CVE → CWE → CAPEC → Technique relationships
  - Lists weaknesses and attack patterns for each CAPEC
  - Displays relationship counts and coverage
  - Human-readable output for understanding graph structure

- `verify_defense_layers.py` — Display defense/detection/deception coverage
  - For each ATT&CK technique: show upstream (CAPEC, CWE) and downstream (defenses)
  - Lists D3FEND mitigations
  - Lists CAR detection analytics
  - Lists SHIELD deception techniques
  - Shows coverage gaps

---

## Running Verification Scripts

```bash
# Visual inspection of causal chain
python tests/verification/verify_causal_chain.py

# Visual inspection of defense coverage
python tests/verification/verify_defense_layers.py

# From tests directory
cd tests/verification && python verify_causal_chain.py
```

---

## Expected Output

**verify_causal_chain.py:**
```
Causal Chain Analysis
====================

CAPEC-242: Code Injection
  ├─ Exploits CWE-94, CWE-95, CWE-96
  ├─ Implements ATT&CK Technique T1059
  │   └─ Relates to 3 other techniques
  └─ Demonstrated by 5 CVEs

[Detailed breakdown continues...]
```

**verify_defense_layers.py:**
```
Defense Coverage Analysis
=========================

T1059: Command and Scripting Interpreter
  ├─ Upstream: CAPEC-242 (Code Injection)
  ├─ Mitigated by D3FEND: 3 techniques
  ├─ Detected by CAR: 2 analytics
  └─ Countered by SHIELD: 1 technique

[Detailed coverage for each technique...]
```

---

## Use Cases

✅ **Before committing changes:** "Does the chain look right?"  
✅ **During development:** "Are relationships being created?"  
✅ **Debugging:** "Why isn't this connection showing?"  
✅ **Understanding:** "What defenses exist for this technique?"  
✅ **Gap analysis:** "Which techniques lack defense coverage?"

---

## Key Differences from Automated Tests

| Aspect | Automated Tests | Verification Scripts |
|--------|-----------------|----------------------|
| **Purpose** | Validate that required relationships exist | Understand why relationships exist |
| **Exit Code** | 0 (pass) or 1 (fail) | Always 0 (informational) |
| **Output** | Pass/Fail + errors | Human-readable chains |
| **Usage** | CI/CD gates | Developer exploration |
| **When** | Before committing | During debugging |

---

## Workflow Example

1. **Make ETL changes:**
   ```bash
   vim src/etl/etl_capec.py  # Modify CAPEC transformer
   ```

2. **Run ETL to generate output:**
   ```bash
   python -m src.etl.etl_capec \
     --input data/capec/samples/sample_capec.json \
     --output tmp/sample_capec.ttl
   ```

3. **Visual inspection:**
   ```bash
   python tests/verification/verify_causal_chain.py  # Does it look right?
   ```

4. **Automated validation:**
   ```bash
   pytest tests/unit/test_etl_pipeline.py::test_capec_etl  # Does it pass SHACL?
   ```

5. **If both good, commit:**
   ```bash
   git commit -am "feat: enhance CAPEC mapping"
   ```

---

## Important Notes

⚠️ **These are not CI/CD tests.** They always exit with code 0.  
⚠️ **Output requires manual interpretation.** Use before automated testing.  
✅ **Safe to run anytime.** No side effects, purely informational.  
✅ **Helpful for debugging.** Shows what's actually in the graph.
