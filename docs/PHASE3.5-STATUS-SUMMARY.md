# PHASE 3.5 STATUS SUMMARY

## Phase 3.5 Execution Plan: Complete Breakdown ✅

Here's the overview of a **36-item detailed execution plan** organized by week with specific, measurable acceptance criteria:

### **Week 1: OCSF Normalizer (Items 1–9)**

**Goal:** Transform Splunk SIEM events → OCSF JSON with confidence scoring, store in Redis

| Step | Task | Acceptance Criteria |
| ---- | ---- | ------------------- |
| 1 | Setup project structure | src/ingest/ocsf_normalizer.py, requirements.txt updated, data/ocsf/samples/, Redis config |
| 2 | OCSF schema definition | OCSFEvent dataclass, JSON schema file |
| 3 | Splunk parser | SplunkNormalizer class extracts metadata, event_category, fields |
| 4 | Confidence scoring | 0.9+ explicit, 0.7-0.9 behavior match, 0.5-0.7 plausible, rule catalog created |
| 5 | Redis client | RedisEventStore class with 30-day TTL, hourly bucketing |
| 6 | CLI & args | --input, --output, --redis-host, --redis-port, --ttl-days flags |
| 7 | Unit tests | 100 events parsed, scored, stored without error |
| 8 | Sample data | 100 real Splunk events (T1059, T1071, T1021) with ground truth confidence |
| **9** | **Milestone** | **1000 events normalized, zero errors** ✅ |

---

### **Week 2: Query Bridge (Items 10–21)**

**Goal:** Join Core KG (Neo4j) + Redis events for investigation, <500ms query latency

| Step | Task | Acceptance Criteria |
| ---- | ---- | ------------------- |
| 10 | Setup bridge structure | src/core/query_bridge.py, Neo4j + Redis pooling |
| 11 | Neo4j connection pool | Lazy init, context managers, existing KG connectivity verified |
| 12 | Redis event retrieval | get_events_in_window(technique_id, hours=24) sorted by timestamp |
| 13 | Cypher traversal 1 | technique_to_cves() returns CVEs with causal path (Technique←CAPEC←CWE←CVE) |
| 14 | Cypher traversal 2 | affected_platforms() returns version bounds + config status |
| 15 | investigate_technique() | Fetches Redis events + Core KG CVEs, returns InvestigationResult |
| 16 | recommend_mitigations() | D3FEND + CAR suggestions with sophistication/availability |
| 17 | Performance tuning | Benchmark <500ms on 24h window (1000+ events), profile queries |
| 18 | Error handling | Redis timeouts, Neo4j failures, missing IDs → graceful errors |
| 19 | Unit tests | Cypher methods mocked, 100% coverage, join correctness |
| 20 | Integration test | Real Core KG + 100 Redis events, causal chains verified |
| **21** | **Milestone** | **investigate_technique('T1059', 24h) <500ms with complete chain** ✅ |

---

### **Week 3: Agent Investigation Layer (Items 22–36)**

**Goal:** LLM + RAG agent that investigates techniques and recommends defenses with provenance

| Step | Task | Acceptance Criteria |
| ---- | ---- | ------------------- |
| 22 | Agent infrastructure | SecurityInvestigationAgent class, interface defined, LLM mocked |
| 23 | Investigation orchestration | agent.investigate(event_id) → Investigation object with causal path |
| 24 | CVE linking | agent._link_cves() returns CVEs + CWE root causes + CVSS + platforms |
| 25 | Recommendation engine | agent.recommend_mitigations() D3FEND + CAR prioritized |
| 26 | Explanation generation | Format: "T1059 exploits CWE-94 via CVE-2025-1234 (per NVD+MITRE)" |
| 27 | Confidence calculation | Product of authoritative (1.0) × observed (0.5-1.0) confidence |
| 28 | Hallucination guardrails | Validate all IDs exist in KG, reject confidence <0.5, log rejections |
| 29 | Unit tests | Investigate/recommend/_link_cves tested, 100% coverage, hallucination tests |
| 30 | E2E integration | Splunk event → normalize → Redis → bridge → agent → investigation |
| 31 | Sample scenarios | 3 realistic examples (C2 beaconing, lateral move, data exfil) |
| 32 | API sketch | FastAPI endpoints for /investigate/{technique_id}, /recommend/{technique_id} |
| 33 | Documentation | OCSF-INTEGRATION.md with architecture, usage, examples, troubleshooting |
| **34** | **Milestone** | **Agent answers: "Why T1059?" → "CWE-94 via CVE-2025-1234" (with provenance)** ✅ |
| 35 | MVP acceptance | All success criteria met, CI smoke tests pass |
| **36** | **Completion** | **Phase 3.5 🟢 Complete, update status file** ✅ |

---

### **Success Criteria (Measurable)**

✅ **Week 1:** Normalizer processes 1000 Splunk events without error  
✅ **Week 2:** Query bridge responds in <500ms on 24-hour window  
✅ **Week 3:** Agent answers with confidence scores + provenance citations  

---

### **How to Use This Plan**

1. **Start Week 1:** Mark item #1 as `in-progress`, complete items 1–9 sequentially
2. **Verify milestone:** Run `python -m src.ingest.ocsf_normalizer --input data/ocsf/samples/splunk_events_1000.ndjson` → zero errors = ✅
3. **Move to Week 2:** Mark items 10–21, verify benchmark <500ms
4. **Move to Week 3:** Mark items 22–36, test E2E (Splunk → Agent) before "done"

---
