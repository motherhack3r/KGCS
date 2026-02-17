# Expert architecture decision for integrating OCSF with our Core KG and agent

- [Expert architecture decision for integrating OCSF with our Core KG and agent](#expert-architecture-decision-for-integrating-ocsf-with-our-core-kg-and-agent)
  - [🎯 Decision: Optimized SIEM+OCSF Integration](#-decision-optimized-siemocsf-integration)
    - [**My Choices (Reasoned)**](#my-choices-reasoned)
  - [📐 Phase 3.5 Architecture](#-phase-35-architecture)
  - [🛠️ Implementation Plan (Phase 3.5)](#️-implementation-plan-phase-35)
    - [**Week 1: OCSF Normalizer**](#week-1-ocsf-normalizer)
    - [**Week 2: Query Bridge**](#week-2-query-bridge)
    - [**Week 3: Agent Reasoning Layer**](#week-3-agent-reasoning-layer)
  - [✅ Success Criteria (MVP Definition of Done)](#-success-criteria-mvp-definition-of-done)
  - [🎯 Why This Design Wins](#-why-this-design-wins)

## 🎯 Decision: Optimized SIEM+OCSF Integration

### **My Choices (Reasoned)**

1. **Data Retention: 30-day rolling window**

   - Incident timelines often span 7-14 days (attackers are slow)
   - 24h is insufficient for multi-stage correlation
   - Redis holds 30d; cold storage archives older
   - **Cost/benefit:** Max incident context, practical compliance, manageable infra

2. **Real-Time Mode: Hybrid (Batch + Streaming)**

   - Agent reasoning (graph queries) = 200-400ms (not sub-second)
   - Rule-based alerting (Kafka) = <5 seconds practical
   - Analysis mode (hourly digests) = sufficient for threat investigation
   - **Rationale:** Gets agent productive in weeks, not months. Layers complexity smartly.

3. **Privacy: Metadata-only in KG, sensitive data in Redis**

   - Graph stores: `eventType`, `confidence`, `timestamp`, `techniqueId`
   - Redis stores: `sourceIP`, `targetDomain`, `userName` (with 30d TTL)
   - Compliant + searchable + separation of concerns
   - **Benefit:** GDPR/SOC compliance, portable KG

4. **Scope: Start Splunk, design for multi-SIEM**

   - Splunk is most common in enterprises
   - Abstraction layer (`src/ingest/ocsf_normalizer.py`) handles any SIEM→OCSF
   - **No rework path:** Add Elasticsearch/ArcSight/QRadar later without touching agent

5. **Agent Capability: Investigate + Recommend (with confidence)**

   - Investigate: "Show me CVEs that explain this technique"
   - Recommend: "Apply these D3FEND mitigations, CAR detections"
   - Confidence scoring prevents hallucination
   - **Out of scope (for now):** Auto-response (requires SOAR approval workflows)

---

## 📐 Phase 3.5 Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                          SPLUNK SIEM                            │
│  (Real-time event stream: 5K+ events/sec)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │ OCSF JSON (normalized)
                         ▼
        ┌────────────────────────────────────┐
        │  src/ingest/ocsf_normalizer.py     │
        │  • Parse OCSF event schema         │
        │  • Extract observables             │
        │  • Enrich with Technique linkage   │
        └────┬───────────────────────────────┘
             │ Buffered OCSF messages
             ▼
    ┌────────────────────────────────┐
    │   Redis (30-day rolling)       │
    │  • Sensitive data (IPs, etc)   │
    │  • Event metadata + confidence │
    │  • Kafka topic buffer          │
    └────┬──────────────────┬────────┘
         │                  │
    [Real-time]         [Batch]
    <5 sec               hourly
         │                  │
         ▼                  ▼
  Kafka Rules        Batch Analysis
  (alerting)         (investigation)
         │                  │
         └────────┬─────────┘
                  │
                  ▼
        ┌────────────────────────────────┐
        │   Neo4j (Core KG only)         │
        │  • CVE, CWE, CAPEC, ATT&CK     │
        │  • D3FEND, CAR, SHIELD, ENGAGE │
        │  • Immutable + authoritative   │
        └────────┬─────────────────────┘
                 │
    ┌────────────┴────────────┐
    │  Query Bridge Layer     │
    │  (Cypher + Redis join)  │
    └────────────┬────────────┘
                 │
                 ▼
        ┌────────────────────────────────┐
        │   Agent (LLM + RAG)            │
        │  • Investigate: Graph queries  │
        │  • Recommend: Confidence score │
        │  • Explain: Causal path        │
        └────────────────────────────────┘
```

---

## 🛠️ Implementation Plan (Phase 3.5)

### **Week 1: OCSF Normalizer**

```python
# src/ingest/ocsf_normalizer.py
class OCSFNormalizer:
    """SPLUNK/ELK → OCSF JSON → (Redis + KG bridge)"""
    
    def normalize(self, siem_event: dict) -> OCSFEvent:
        """Transform SIEM event to OCSF schema."""
        # Splunk _raw → OCSF fields
        # Map to Technique (best-guess from event signature)
        # Store in Redis with TTL=30d
        
    def link_technique(self, event: OCSFEvent) -> Tuple[TechniqueId, float]:
        """Match event signature to ATT&CK technique.
        
        Returns: (technique_id, confidence: 0.0-1.0)
          - 0.9+: Signature explicitly mentions technique
          - 0.7-0.9: Behavior matches known technique
          - 0.5-0.7: Plausible but uncertain
        """
```

### **Week 2: Query Bridge**

```python
# src/core/query_bridge.py
class QueryBridge:
    """Join Core KG + Redis event data"""
    
    def investigate_technique(self, technique_id: str, 
                            time_window: str = "24h") -> InvestigationResult:
        """
        1. Fetch Core KG: Technique → CWE → CVE → Platforms
        2. Fetch Redis: Recent events matching this Technique
        3. Join: "What platforms are vulnerable? Which were hit?"
        """
        
    def recommend_mitigations(self, technique_id: str, 
                             platforms: List[str]) -> List[Mitigation]:
        """D3FEND + CAR recommendations for this technique + affected platforms"""
```

### **Week 3: Agent Reasoning Layer**

```python
# src/rag/agent.py
class SecurityInvestigationAgent:
    """Investigate observed techniques against KG"""
    
    def investigate(self, event_id: str) -> Investigation:
        """
        User: "What is event XYZ-123?"
        Agent:
          1. Fetch event from Redis (OCSF + confidence)
          2. Query bridge: Link to CVE, CWE, defenses
          3. Return: {
               observed_technique: "T1059",
               confidence: 0.85,
               root_causes: [CVE-2025-1234, CVE-2025-5678],
               defenses: [D3FEND-PA-001, CAR-2020-04-001],
               explanation: "Technique T1059 exploits CWE-94 via CVE-2025-1234..."
             }
        """
```

---

## ✅ Success Criteria (MVP Definition of Done)

**Week 1 Deliverable:**

- [ ] OCSF normalizer handles 1000 Splunk events without error
- [ ] Confidence scoring matches manual validation (spot-check 20 events)
- [ ] Redis stores events with 30d TTL

**Week 2 Deliverable:**

- [ ] Query bridge joins Core KG + Redis without N+1 queries
- [ ] `investigate_technique("T1059", "24h")` returns <500ms
- [ ] Recommendations include all D3FEND + CAR paths

**Week 3 Deliverable:**

- [ ] Agent answers: "Why was T1059 detected? What CVEs enable it?"
- [ ] Explanations cite MITRE + NVD sources
- [ ] Confidence scores explain uncertainty

---

## 🎯 Why This Design Wins

| Aspect | Benefit |
| ------ | ------- |
| **Separation** | Core KG frozen; SIEM data ephemeral |
| **Speed** | Hourly batch + <5s alerting covers both modes |
| **Compliance** | Metadata in KG, sensitive data in TTL Redis |
| **Scalability** | Multi-SIEM ready (just add normalizer) |
| **Agent UX** | Investigation (high value) + recommendations (actionable) |
| **Safety** | Confidence scoring prevents false positives |

---

**Ready to code?** Should I:

1. **Start Phase 3.5 plan** (detailed breakdown with todo list)?
2. **Sketch OCSF schema mapping** (Splunk fields → OCSF → RDF)?
3. **Design Redis keys + TTL strategy** (data structures for query efficiency)?
4. **Create sample event** (Splunk → OCSF → Technique linking)?

What's your priority?
