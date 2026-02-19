# AI Cybersecurity Agent Architecture on Azure

Going **From Graph-RAG Design to Terraform Deployment**

---

## 1. Architectural Decision: Why Graph-RAG

### 1.1 Context

You already have:

* A formal OWL ontology
* Integrated standards (CVE, CWE, CAPEC, ATT&CK, D3FEND, ENGAGE, CAR)
* ETL pipelines
* SHACL validation
* RDF generation
* Graph loaded into Neo4j

This means your system already contains **structured, validated, multi-hop knowledge**.

The correct architectural pattern is therefore:

> **Graph-RAG (Graph-based Retrieval Augmented Generation)**

Not:

* Fine-tuning a model
* Embedding-only search
* Training a domain-specific LLM

---

### 1.2 Why Not Fine-Tuning?

Fine-tuning:

* Changes language behavior
* Does not improve structured reasoning
* Does not replace ontology-backed logic
* Introduces lifecycle and retraining complexity

Your knowledge is already structured and validated. The model should **query and reason over it**, not internalize it.

---

### 1.3 Why Graph-RAG?

Graph-RAG enables:

* Multi-hop reasoning across relationships
* Deterministic retrieval
* Reduced hallucination
* Explainability (explicit traversal paths)
* Security control (schema-limited queries)

It is ideal for cybersecurity knowledge graphs built from:

* MITRE
* National Vulnerability Database
* National Institute of Standards and Technology

---

## 2. System Architecture Overview

### 2.1 High-Level Flow

```text
User / API / Scheduler
        ↓
LLM (Planner + Reasoner)
        ↓
Graph Query Tool (Cypher)
        ↓
Neo4j
        ↓
Structured Result
        ↓
LLM Response Generation
```

The LLM acts as:

* Intent interpreter
* Query planner
* Explanation generator

The graph remains the **source of truth**.

---

## 3. Azure Production Architecture

### 3.1 Core Services

| Function          | Azure Service                   |
| ----------------- | ------------------------------- |
| LLM               | Azure OpenAI                    |
| Agent Runtime     | Azure Container Apps            |
| Graph Database    | Neo4j (Aura or VM)              |
| Secrets           | Azure Key Vault                 |
| Raw Data          | Azure Blob Storage              |
| ETL Orchestration | Azure Data Factory / Databricks |
| Observability     | Azure Monitor + Log Analytics   |
| API Exposure      | Azure API Management            |

---

### 3.2 Networking Model

All services are deployed in a **private VNet**.

#### VNet Structure

```text
VNet: cyber-ai-vnet
│
├── subnet-app       (Container Apps)
├── subnet-data      (Neo4j VM if used)
├── subnet-ai        (Private Endpoints - OpenAI)
├── subnet-pe        (Private Endpoints - Key Vault, Storage)
```

#### Security Principles

* Public network access disabled
* Private Endpoints for:

  * Azure OpenAI
  * Key Vault
  * Storage
* No public IPs for data services
* Optional Azure Firewall for egress control

---

## 4. Security Model

### 4.1 Identity

All services use **Managed Identity**.

Example:

* Container App → calls Azure OpenAI
* Container App → retrieves secrets from Key Vault
* Data Factory → writes to Storage

No embedded credentials.

---

### 4.2 RBAC Model

#### Azure RBAC Roles

| Role                   | Permissions                                     |
| ---------------------- | ----------------------------------------------- |
| AI-Agent-Operator      | Key Vault Secrets User, Cognitive Services User |
| Data-Pipeline-Operator | Storage Contributor, Data Factory Contributor   |
| Security-Auditor       | Reader + Log Analytics                          |

---

### 4.3 Neo4j Role Model

| Role            | Permissions |
| --------------- | ----------- |
| agent_reader    | MATCH only  |
| pipeline_writer | WRITE       |
| admin           | FULL        |

The AI agent must be read-only.

---

## 5. Agent Design

### 5.1 Required Tools

#### Tool: query_graph

Input:

```json
{
  "cypher": "...",
  "params": {}
}
```

Output:

```json
{
  "nodes": [],
  "relationships": []
}
```

---

### 5.2 Schema Injection

The LLM must receive a simplified schema:

```text
Node Labels:
- CVE
- CWE
- CAPEC
- Technique
- Countermeasure

Relationships:
- (CVE)-[:HAS_WEAKNESS]->(CWE)
- (CWE)-[:RELATED_TO]->(CAPEC)
- (CAPEC)-[:IMPLEMENTS]->(Technique)
- (Technique)-[:MITIGATED_BY]->(Countermeasure)
```

This constrains Cypher generation.

---

### 5.3 Multi-Hop Reasoning Pattern

Instead of large queries:

1. Query CVE
2. Validate results
3. Query CWE
4. Continue traversal
5. Build explainable reasoning path

This improves:

* Reliability
* Observability
* Confidence scoring

---

## 6. Observability

Enable diagnostics for:

* Azure OpenAI
* Container Apps
* Storage
* API Management

Monitor:

* LLM latency
* Query execution time
* Tool-calling errors
* Token usage
* Cost per request

---

## 7. Terraform Deployment Template

Below is a simplified production-ready baseline.

---

### 7.1 versions.tf

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110"
    }
  }
}
```

---

### 7.2 providers.tf

```hcl
provider "azurerm" {
  features {}
}
```

---

### 7.3 Resource Group

```hcl
resource "azurerm_resource_group" "rg" {
  name     = "rg-cyber-ai-${var.environment}"
  location = var.location
}
```

---

### 7.4 Virtual Network

```hcl
resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-cyber-ai-${var.environment}"
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  address_space       = ["10.10.0.0/16"]
}
```

---

### 7.5 Azure OpenAI (Private)

```hcl
resource "azurerm_cognitive_account" "openai" {
  name                          = "aoai-cyber-${var.environment}"
  location                      = var.location
  resource_group_name           = azurerm_resource_group.rg.name
  kind                          = "OpenAI"
  sku_name                      = "S0"
  public_network_access_enabled = false
}
```

---

### 7.6 Container App (Agent)

```hcl
resource "azurerm_container_app" "agent" {
  name                         = "agent-cyber-${var.environment}"
  resource_group_name          = azurerm_resource_group.rg.name
  container_app_environment_id = azurerm_container_app_environment.env.id
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  template {
    container {
      name   = "agent"
      image  = var.image_name
      cpu    = 1
      memory = "2Gi"
    }
  }

  ingress {
    external_enabled = false
    target_port      = 8000
  }
}
```

---

### 7.7 Key Vault

```hcl
resource "azurerm_key_vault" "kv" {
  name                          = "kv-cyber-${var.environment}"
  location                      = var.location
  resource_group_name           = azurerm_resource_group.rg.name
  tenant_id                     = data.azurerm_client_config.current.tenant_id
  sku_name                      = "standard"
  public_network_access_enabled = false
}
```

---

### 7.8 Storage

```hcl
resource "azurerm_storage_account" "storage" {
  name                          = "stcyber${var.environment}"
  resource_group_name           = azurerm_resource_group.rg.name
  location                      = var.location
  account_tier                  = "Standard"
  account_replication_type      = "LRS"
  public_network_access_enabled = false
}
```

---

## 8. Final Architecture Summary

You are not building a chatbot.

You are building:

> A structured reasoning system over a formally validated cybersecurity ontology deployed securely on Azure.

Core principles:

* Graph-RAG over structured ontology
* Private networking
* Managed Identity
* Least-privilege RBAC
* Deterministic graph retrieval
* LLM as reasoning layer, not knowledge store

---

If needed, the next step would be:

* A full production Terraform module set (network isolation, NSGs, Firewall, DDoS, CMK)
* Or a STRIDE-based threat model for this architecture.
