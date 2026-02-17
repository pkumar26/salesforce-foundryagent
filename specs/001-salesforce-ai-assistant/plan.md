# Implementation Plan: Salesforce AI Assistant

**Branch**: `001-salesforce-ai-assistant` | **Date**: 2026-02-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-salesforce-ai-assistant/spec.md`

## Summary

Build an end-to-end AI assistant using **Microsoft Agent Framework** on **Azure AI Foundry** that orchestrates domain-specific agents (Sales Agent, Service Agent) via **MCP servers** integrated with **Salesforce CRM**. The assistant is delivered through **Microsoft Teams** and supports meeting prep, pipeline risk analysis, case triage, knowledge search, and natural-language CRM queries — all grounded in live Salesforce data with per-user OAuth 2.0 delegated authentication.

**Technical approach**: Python 3.11+ notebooks demonstrate each scenario end-to-end using `azure-ai-projects` SDK to create Foundry Agents with MCP tool connections to two FastMCP-based servers (`salesforce-crm` with 13 tools, `salesforce-knowledge` with 2 tools). Salesforce access is via `simple-salesforce` with REST API v62.0. Infrastructure is provisioned via modular **Bicep** templates with `.bicepparam` environment parameterization and deployed through **GitHub Actions** CI/CD pipelines.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `azure-ai-projects`, `azure-identity`, `simple-salesforce`, `mcp[cli]`, `fastmcp`, `pydantic`, `httpx`, `python-dotenv`
**Storage**: N/A — Salesforce is system of record; Azure AI Search for Knowledge Article RAG
**Testing**: `pytest` + `pytest-asyncio`; contract tests for MCP tools
**Target Platform**: Azure AI Foundry (cloud agents); notebooks local or Azure ML Compute
**Project Type**: Single project with modular MCP servers
**Performance Goals**: Simple queries < 5s, complex < 15s (P95)
**Constraints**: < 50 concurrent users; Salesforce API daily limits; Azure OpenAI token limits
**Scale/Scope**: < 500 total users (demo-first)
**Infrastructure**: Bicep IaC with multi-environment support (dev, test, prod); GitHub Actions CI/CD

## Constitution Check (Pre-Design)

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| I | Integration-First Architecture | ✅ PASS | MCP servers expose well-defined JSON Schema contracts per tool. All Salesforce object dependencies documented in data-model.md. OAuth 2.0 per-user auth via Connected Apps — no hard-coded credentials. Data flow direction documented per object. |
| II | Security & Compliance by Default | ✅ PASS | Per-user delegated OAuth enforces FLS/sharing rules natively. PII confined to Salesforce (no caching). TLS 1.2+ in transit, Key Vault for secrets. Least-privilege scopes: `api`, `refresh_token`, `openid`. |
| III | AI-Responsible & Human-in-the-Loop | ✅ PASS | All write-backs require explicit user confirmation (FR-007). Responses cite Salesforce record IDs (FR-011). Azure AI Content Safety enabled on all deployments. System prompts enforce grounding constraints. |
| IV | Iterative Delivery & Phased Rollout | ✅ PASS | 4-phase plan: Foundation → MCP → Agent Integration → Polish. Notebooks as POC deliverables per phase. Go/no-go criteria per phase. |
| V | Operational Excellence & Observability | ✅ PASS | Application Insights for telemetry. Per-session API call tracking in `salesforce_client.py`. Structured error responses with error codes. Provisioned via observability Bicep module. |

**Gate result**: PASS — proceed to Phase 0.

## Constitution Scope Exceptions (Demo Phase)

The following constitution requirements are formally deferred for the demo-first deployment (< 50 users). They MUST be addressed before scaling to production.

| Principle | Constitution Requirement | Exception | Rationale |
|-----------|------------------------|-----------|----------|
| I | Azure API Management as primary integration channel | Deferred to production phase | Demo-first deployment (< 50 users) uses direct Salesforce REST via `simple-salesforce`. APIM will be added when scaling beyond demo. Rate limiting is enforced in application code (`salesforce_client.py`). |
| I | MuleSoft as optional middleware | Not applicable | Direct REST integration selected per plan. |
| IV | 4-week production Pilot | Replaced with structured validation phase | Demo-first posture uses notebook-based validation with representative scenarios before expanding to production users. |
| V | Salesforce Platform Events for integration monitoring | Deferred to production phase | Demo phase uses direct REST polling. Platform Events will be added for near-real-time CRM event capture when scaling to production. |

### Environment Consolidation Note

The constitution defines 4 environments (Dev, QA, UAT, Prod). This plan consolidates to 3 (dev, test, prod) because:
- **QA and UAT are merged into `test`**: At demo-first scale (< 50 users), a single test environment covers both integration testing and user acceptance. The `test` environment uses a Salesforce Partial Copy Sandbox that serves both QA and UAT purposes.
- **Separate QA/UAT will be introduced** when scaling to production with distinct user groups requiring isolated acceptance testing.

## Project Structure

### Documentation (this feature)

```text
specs/001-salesforce-ai-assistant/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── mcp-salesforce-crm.md       # 13 CRM tool contracts
│   ├── mcp-salesforce-knowledge.md # 2 Knowledge tool contracts
│   └── bicep-modules.md            # Bicep module parameter/output contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
salesforce-foundryagent/
├── agents/
│   ├── sales/
│   │   └── system_prompt.md            # Sales Agent instructions
│   └── service/
│       └── system_prompt.md            # Service Agent instructions
│
├── mcp_servers/
│   ├── salesforce_crm/
│   │   ├── __init__.py
│   │   ├── server.py                   # FastMCP server (13 tools)
│   │   └── tools/
│   │       ├── accounts.py             # get_account, search_accounts
│   │       ├── contacts.py             # get_contacts_for_account
│   │       ├── opportunities.py        # get_opportunities, get_pipeline_summary
│   │       ├── cases.py                # get_case, create_case, update_case
│   │       ├── activities.py           # get_recent_activities, create_task
│   │       ├── leads.py                # get_leads, update_lead_status
│   │       └── users.py               # get_team_members
│   └── salesforce_knowledge/
│       ├── __init__.py
│       ├── server.py                   # FastMCP server (2 tools)
│       └── tools/
│           └── articles.py             # search_articles, get_article_by_id
│
├── shared/
│   ├── __init__.py
│   ├── models.py                       # Pydantic response models
│   ├── salesforce_client.py            # SF REST wrapper + rate tracking
│   ├── auth.py                         # OAuth flow helpers
│   └── config.py                       # Environment + config loader
│
├── notebooks/
│   ├── 01_sales_pipeline_summary.ipynb
│   ├── 02_sales_account_briefing.ipynb
│   ├── 03_service_case_triage.ipynb
│   └── 04_service_kb_assistant.ipynb
│
├── scripts/
│   ├── bootstrap_env.sh                # Venv + deps + .env setup
│   └── provision_azure.sh              # Wraps `az deployment` with Bicep
│
├── infra/
│   └── bicep/
│       ├── main.bicep                  # Orchestrator — composes all modules
│       ├── env/
│       │   ├── dev.bicepparam          # Dev environment overrides
│       │   ├── test.bicepparam         # Test environment overrides
│       │   └── prod.bicepparam         # Production overrides
│       └── modules/
│           ├── ai-foundry.bicep        # AI Foundry Hub + Project
│           ├── openai.bicep            # Azure OpenAI + GPT-4o deployment
│           ├── ai-search.bicep         # Azure AI Search
│           ├── keyvault.bicep          # Azure Key Vault + access policies
│           ├── storage.bicep           # Storage Account (AI Foundry dependency)
│           ├── app-insights.bicep      # Application Insights + Log Analytics
│           ├── app-service.bicep       # App Service (optional: hosted MCP/SSE)
│           └── bot-service.bicep       # Azure Bot Service (Teams channel)
│
├── .github/
│   └── workflows/
│       ├── deploy-infra.yml            # Bicep deployment per environment
│       └── ci.yml                      # Lint, test, validate
│
├── config/
│   └── risk_thresholds.yaml            # Configurable deal-risk thresholds
│
├── docs/
│   ├── salesforce-setup.md             # Connected App configuration guide
│   ├── azure-setup.md                  # Azure resource setup guide
│   └── extending-scenarios.md          # How to add new MCP tools
│
├── tests/
│   ├── unit/
│   │   ├── test_models.py
│   │   └── test_salesforce_client.py
│   ├── contract/
│   │   ├── test_crm_tools.py
│   │   └── test_knowledge_tools.py
│   └── integration/
│       └── test_agent_e2e.py
│
├── .env.example                        # Template for environment variables
├── requirements.txt                    # Python dependencies
├── pyproject.toml                      # Project metadata
└── README.md
```

**Structure Decision**: Single-project layout with modular MCP servers under `mcp_servers/`. Infrastructure as Code uses a modular Bicep layout under `infra/bicep/` with per-environment `.bicepparam` files. GitHub Actions workflows under `.github/workflows/` handle CI and infrastructure deployment.

---

## Architectural Overview

```text
┌────────────────────────────────────────────────────────────────┐
│                     Microsoft Teams                            │
│                   (Delivery Channel)                           │
└──────────────────────┬─────────────────────────────────────────┘
                       │
              ┌────────▼─────────┐
              │  Orchestrator    │
              │  Agent           │
              │  (Azure AI       │
              │   Foundry)       │
              └───┬──────────┬───┘
                  │          │
         ┌────────▼──┐  ┌───▼────────┐
         │ Sales     │  │ Service    │
         │ Agent     │  │ Agent      │
         └─────┬─────┘  └──────┬─────┘
               │               │
        ┌──────▼───────────────▼──────┐
        │      MCP Protocol           │
        │  (stdio / SSE transport)    │
        └──────┬───────────────┬──────┘
               │               │
    ┌──────────▼──┐     ┌──────▼─────────┐
    │ salesforce- │     │ salesforce-    │
    │ crm         │     │ knowledge     │
    │ (13 tools)  │     │ (2 tools)     │
    └──────┬──────┘     └──────┬────────┘
           │                   │
    ┌──────▼───────────────────▼──────┐
    │  shared/salesforce_client.py   │
    │  (simple-salesforce wrapper)   │
    └──────────────┬─────────────────┘
                   │ Per-user OAuth 2.0
    ┌──────────────▼─────────────────┐
    │       Salesforce CRM           │
    │    (REST API v62.0)            │
    │  Accounts · Contacts · Cases   │
    │  Opportunities · Knowledge     │
    └────────────────────────────────┘

    ┌────────────────────────────────┐
    │       Azure Platform           │
    │  AI Foundry  · OpenAI (GPT-4o)│
    │  AI Search   · Key Vault       │
    │  App Insights · Storage        │
    │  (Provisioned via Bicep IaC)   │
    └────────────────────────────────┘
```

---

## MCP Server Design

### salesforce-crm (13 tools)

| Tool | Category | Direction | Confirmation |
|------|----------|-----------|--------------|
| `get_account` | Account | Read | No |
| `search_accounts` | Account | Read | No |
| `get_contacts_for_account` | Contact | Read | No |
| `get_opportunities` | Opportunity | Read | No |
| `get_pipeline_summary` | Opportunity | Read | No |
| `get_case` | Case | Read | No |
| `create_case` | Case | Write | **Yes** |
| `update_case` | Case | Write | **Yes** |
| `get_recent_activities` | Activity | Read | No |
| `create_task` | Activity | Write | **Yes** |
| `get_leads` | Lead | Read | No |
| `update_lead_status` | Lead | Write | **Yes** |
| `get_team_members` | User | Read | No |

Full input/output JSON schemas: [contracts/mcp-salesforce-crm.md](contracts/mcp-salesforce-crm.md)

### salesforce-knowledge (2 tools)

| Tool | Category | Direction |
|------|----------|-----------|
| `search_articles` | Knowledge | Read |
| `get_article_by_id` | Knowledge | Read |

Full schemas: [contracts/mcp-salesforce-knowledge.md](contracts/mcp-salesforce-knowledge.md)

### Error Handling

All tools return a standard error envelope: `{ "error": { "code": "...", "message": "..." } }` with codes: `NOT_FOUND`, `PERMISSION_DENIED`, `RATE_LIMIT_WARNING`, `RATE_LIMIT_EXCEEDED`, `INVALID_INPUT`, `SF_API_ERROR`, `AUTH_ERROR`, `KNOWLEDGE_DISABLED`.

---

## Notebook Design

Each notebook is a self-contained scenario demonstrating one user story end-to-end.

### Notebook 1: Sales Pipeline Summary (`01_sales_pipeline_summary.ipynb`)

**User Story**: US2 (Pipeline Summary & Risk Flagging)
**Persona**: Sales Manager

| Cell # | Type | Purpose |
|--------|------|---------|
| 1 | Markdown | Title, description, prerequisites |
| 2 | Code | Environment check: load `.env`, validate required vars |
| 3 | Code | Authenticate: `DefaultAzureCredential()`, create `AIProjectClient` |
| 4 | Code | Configure MCP: `McpToolConnection` with salesforce-crm server (stdio) |
| 5 | Code | Create Sales Agent with system prompt and MCP toolset |
| 6 | Code | Create thread, send "Show my team's pipeline and flag at-risk deals" |
| 7 | Code | Process run, display response with risk-flagged deals |
| 8 | Code | Follow-up: "What should Sarah focus on this week?" |
| 9 | Code | Cleanup: delete agent, close connections |

### Notebook 2: Account Meeting Briefing (`02_sales_account_briefing.ipynb`)

**User Story**: US1 (Meeting Preparation)
**Persona**: Account Executive

| Cell # | Type | Purpose |
|--------|------|---------|
| 1 | Markdown | Title, description |
| 2 | Code | Environment + auth setup |
| 3 | Code | MCP connection: salesforce-crm |
| 4 | Code | Create Sales Agent |
| 5 | Code | "Prepare me for my meeting with Acme Corp" |
| 6 | Code | Display briefing: account, contacts, opportunities, activities, talking points |
| 7 | Code | Follow-up: "Any other open opportunities with them?" |
| 8 | Code | Cleanup |

### Notebook 3: Case Triage (`03_service_case_triage.ipynb`)

**User Story**: US3 (Case Triage & Response)
**Persona**: CSR

| Cell # | Type | Purpose |
|--------|------|---------|
| 1 | Markdown | Title, description |
| 2 | Code | Environment + auth (both MCP servers needed) |
| 3 | Code | MCP connections: salesforce-crm + salesforce-knowledge |
| 4 | Code | Create Service Agent |
| 5 | Code | "Triage case #12345 and suggest a response" |
| 6 | Code | Display triage: priority, category, draft response, KB citations |
| 7 | Code | User confirms: "Apply this triage" → write-back |
| 8 | Code | Verify update in Salesforce |
| 9 | Code | Cleanup |

### Notebook 4: Knowledge Base Assistant (`04_service_kb_assistant.ipynb`)

**User Story**: US4 (Natural-Language CRM Query) + US3 (KB search)
**Persona**: CSR

| Cell # | Type | Purpose |
|--------|------|---------|
| 1 | Markdown | Title, description |
| 2 | Code | Environment + auth |
| 3 | Code | MCP connection: salesforce-knowledge |
| 4 | Code | Create Service Agent |
| 5 | Code | "How do I reset a customer's API key?" |
| 6 | Code | Display KB article results with citations |
| 7 | Code | Follow-up: "What about SSO configuration?" |
| 8 | Code | Cleanup |

---

## Infrastructure as Code (Bicep) Strategy

### Design Principles

1. **Modular composition**: One Bicep module per Azure resource type. `main.bicep` orchestrates all modules.
2. **Environment parameterization**: `.bicepparam` files per environment (dev, test, prod) — no JSON parameter files.
3. **Least-privilege defaults**: Dev uses minimal SKUs; prod uses production-grade tiers with diagnostics.
4. **Idempotent deployments**: All resources use `existing` references where needed; modules safe to re-run.
5. **Azure Verified Module patterns**: Follow AVM naming, tagging, and diagnostic settings conventions.
6. **Security-first**: Use `@secure()` decorator on all sensitive parameters. Key Vault Premium (HSM) in prod. OIDC for CI/CD — no stored credentials.
7. **Typed parameters**: Use User-defined types and `.bicepparam` files (not JSON). Avoid open `object` or `array` types.

### Bicep Module Architecture

```text
infra/bicep/
├── main.bicep              # Orchestrator: composes all modules
├── main.bicepparam         # Shared default parameters (used by dev)
├── env/
│   ├── dev.bicepparam      # Dev: minimal SKUs, no App Service
│   ├── test.bicepparam     # Test: mid-tier SKUs, optional App Service
│   └── prod.bicepparam     # Prod: production SKUs, App Service, diagnostics
└── modules/
    ├── ai-foundry.bicep    # AI Foundry Hub + Project
    ├── openai.bicep        # Azure OpenAI Service + GPT-4o deployment
    ├── ai-search.bicep     # Azure AI Search index
    ├── keyvault.bicep      # Key Vault + access policies
    ├── storage.bicep       # Storage Account (AI Foundry dependency)
    ├── app-insights.bicep  # Application Insights + Log Analytics workspace
    └── app-service.bicep   # App Service Plan + Web App (hosted MCP/SSE)
```

### Module Dependency Graph

```text
                    ┌──────────────┐
                    │  main.bicep  │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────────┐
          │                │                    │
    ┌─────▼──────┐   ┌─────▼──────┐   ┌────────▼────────┐
    │  storage   │   │  keyvault  │   │  app-insights   │
    └─────┬──────┘   └─────┬──────┘   └────────┬────────┘
          │                │                    │
          │          ┌─────▼──────┐             │
          ├──────────► ai-foundry ◄─────────────┤
          │          └─────┬──────┘             │
          │                │                    │
          │          ┌─────▼──────┐             │
          │          │   openai   │             │
          │          └────────────┘             │
          │                                     │
          │          ┌────────────┐             │
          └──────────► ai-search  │             │
                     └────────────┘             │
                                                │
                     ┌────────────┐             │
                     │app-service ◄─────────────┘
                     │ (optional) │
                     └────────────┘
```

### Resource → Environment Matrix

| Azure Resource | Dev | Test | Prod | Purpose |
|---------------|-----|------|------|---------|
| **AI Foundry Hub** | ✅ Mandatory | ✅ Mandatory | ✅ Mandatory | Agent hosting container |
| **AI Foundry Project** | ✅ Mandatory | ✅ Mandatory | ✅ Mandatory | Agent workspace |
| **Azure OpenAI Service** | ✅ Mandatory | ✅ Mandatory | ✅ Mandatory | GPT-4o model host |
| **GPT-4o Deployment** | ✅ Mandatory | ✅ Mandatory | ✅ Mandatory | Agent model |
| **Azure AI Search** | ✅ Mandatory | ✅ Mandatory | ✅ Mandatory | KB article RAG index |
| **Azure Key Vault** | ✅ Mandatory | ✅ Mandatory | ✅ Mandatory | SF OAuth secrets |
| **Storage Account** | ✅ Mandatory | ✅ Mandatory | ✅ Mandatory | AI Foundry file store |
| **Application Insights** | ⚡ Optional | ✅ Mandatory | ✅ Mandatory | Telemetry |
| **Log Analytics Workspace** | ⚡ Optional | ✅ Mandatory | ✅ Mandatory | Diagnostics |
| **App Service Plan** | ❌ Not deployed | ⚡ Optional | ✅ Mandatory | Hosted MCP (SSE) |
| **App Service (Web App)** | ❌ Not deployed | ⚡ Optional | ✅ Mandatory | MCP server hosting |

**Legend**: ✅ = deployed by default, ⚡ = deployed if `deploy*` param is `true`, ❌ = not deployed

### Environment SKU Strategy

| Resource | Dev | Test | Prod |
|----------|-----|------|------|
| AI Foundry Hub | Standard | Standard | Standard |
| OpenAI Service | S0 | S0 | S0 |
| GPT-4o Deployment | GlobalStandard (10K TPM) | GlobalStandard (30K TPM) | GlobalStandard (80K TPM) |
| AI Search | Free | Basic | Standard |
| Key Vault | Standard | Standard | Premium (HSM) |
| Storage Account | Standard LRS | Standard LRS | Standard ZRS |
| App Insights | — | Standard | Standard |
| App Service Plan | — | B1 (Basic) | S1 (Standard) |

### `.bicepparam` Environment Parameterization

Each `.bicepparam` file uses the Bicep parameters file format to configure environment-specific values:

**`env/dev.bicepparam`** (minimal cost, notebook-only):
```bicep
using '../main.bicep'

param environmentName = 'dev'
param location = 'eastus2'
param projectName = 'sfai-dev'
param openaiModelCapacity = 10              // 10K TPM — dev workload
param aiSearchSku = 'free'
param keyVaultSku = 'standard'
param storageRedundancy = 'LRS'
param deployAppInsights = false             // Optional for dev
param deployAppService = false              // Notebooks only — no hosted MCP
param tags = {
  environment: 'dev'
  project: 'salesforce-ai-assistant'
  managedBy: 'bicep'
}
```

**`env/test.bicepparam`** (integration testing, optional hosted MCP):
```bicep
using '../main.bicep'

param environmentName = 'test'
param location = 'eastus2'
param projectName = 'sfai-test'
param openaiModelCapacity = 30              // 30K TPM
param aiSearchSku = 'basic'
param keyVaultSku = 'standard'
param storageRedundancy = 'LRS'
param deployAppInsights = true
param deployAppService = true               // Hosted MCP for integration tests
param appServiceSkuName = 'B1'
param tags = {
  environment: 'test'
  project: 'salesforce-ai-assistant'
  managedBy: 'bicep'
}
```

**`env/prod.bicepparam`** (production-grade):
```bicep
using '../main.bicep'

param environmentName = 'prod'
param location = 'eastus2'
param projectName = 'sfai-prod'
param openaiModelCapacity = 80              // 80K TPM
param aiSearchSku = 'standard'
param keyVaultSku = 'premium'               // HSM-backed for compliance
param storageRedundancy = 'ZRS'             // Zone-redundant
param deployAppInsights = true
param deployAppService = true
param appServiceSkuName = 'S1'
param tags = {
  environment: 'prod'
  project: 'salesforce-ai-assistant'
  managedBy: 'bicep'
}
```

### `main.bicep` Orchestrator Design

```bicep
// main.bicep — pseudocode structure
targetScope = 'subscription'

// --- Parameters (typed) ---
param environmentName string
param location string
param projectName string
param openaiModelCapacity int
param aiSearchSku string
param keyVaultSku string
param storageRedundancy string
param deployAppInsights bool
param deployAppService bool
param appServiceSkuName string = 'B1'
param tags object  // { environment, project, managedBy }

// --- Resource Group ---
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-${projectName}'
  location: location
  tags: tags
}

// --- Foundation modules (no dependencies) ---
module storage 'modules/storage.bicep' = { scope: rg, params: { ... } }
module keyvault 'modules/keyvault.bicep' = { scope: rg, params: { ... } }
module appInsights 'modules/app-insights.bicep' = if (deployAppInsights) { scope: rg, params: { ... } }

// --- AI modules (depend on foundation) ---
module aiFoundry 'modules/ai-foundry.bicep' = {
  scope: rg
  params: {
    storageAccountId: storage.outputs.storageAccountId
    keyVaultId: keyvault.outputs.keyVaultId
    appInsightsId: deployAppInsights ? appInsights.outputs.appInsightsId : ''
  }
}
module openai 'modules/openai.bicep' = {
  scope: rg
  params: { aiFoundryProjectName: aiFoundry.outputs.projectName, capacity: openaiModelCapacity }
}
module aiSearch 'modules/ai-search.bicep' = { scope: rg, params: { sku: aiSearchSku } }

// --- Optional: App Service for hosted MCP (SSE) ---
module appService 'modules/app-service.bicep' = if (deployAppService) {
  scope: rg
  params: { skuName: appServiceSkuName }
}

// --- Outputs (consumed by provision_azure.sh → .env) ---
output aiFoundryProjectEndpoint string = aiFoundry.outputs.projectEndpoint
output openaiDeploymentName string = openai.outputs.deploymentName
output keyVaultUri string = keyvault.outputs.vaultUri
output storageAccountName string = storage.outputs.storageAccountName
output appInsightsConnectionString string = deployAppInsights ? appInsights.outputs.connectionString : ''
output appServiceUrl string = deployAppService ? appService.outputs.defaultHostName : ''
```

### Deployment Commands

```bash
# Deploy dev environment
az deployment sub create \
  --location eastus2 \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/env/dev.bicepparam

# Deploy test environment
az deployment sub create \
  --location eastus2 \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/env/test.bicepparam

# Deploy prod environment
az deployment sub create \
  --location eastus2 \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/env/prod.bicepparam

# Validate without deploying (what-if)
az deployment sub what-if \
  --location eastus2 \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/env/dev.bicepparam
```

### How Notebooks Reference Provisioned Resources

After Bicep deployment, resource connection strings and endpoints flow to notebooks via the `.env` file:

```text
┌────────────────┐     az deployment     ┌──────────────────┐
│  Bicep Deploy  │ ──────────────────►   │   Azure Resources │
│  (main.bicep)  │                       │   (provisioned)   │
└────────┬───────┘                       └────────┬──────────┘
         │                                        │
         │  outputs (endpoint, keys)              │
         │                                        │
    ┌────▼──────────────┐                         │
    │ provision_azure.sh │ ◄──────────────────────┘
    │ (captures outputs) │   az deployment show --query
    └────────┬───────────┘
             │ writes to
    ┌────────▼───────┐
    │    .env file   │
    │ AZURE_AI_...   │
    │ SF_...         │
    └────────┬───────┘
             │ python-dotenv
    ┌────────▼───────────┐
    │   Notebook Cell 2  │
    │ load_dotenv()      │
    │ os.environ[...]    │
    └────────────────────┘
```

**Key `.env` variables populated from Bicep outputs**:

| Variable | Bicep Output Source | Module |
|----------|-------------------|--------|
| `AZURE_AI_PROJECT_ENDPOINT` | `aiFoundryProjectEndpoint` | `ai-foundry.bicep` |
| `AZURE_OPENAI_DEPLOYMENT` | `openaiDeploymentName` | `openai.bicep` |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | `appInsightsConnectionString` | `app-insights.bicep` |
| `AZURE_KEYVAULT_URL` | `keyVaultUri` | `keyvault.bicep` |
| `AZURE_STORAGE_ACCOUNT_NAME` | `storageAccountName` | `storage.bicep` |

**Salesforce variables** (`SF_CONSUMER_KEY`, `SF_CONSUMER_SECRET`, etc.) are managed manually — they come from the Salesforce Connected App, not Azure provisioning. They are stored in Key Vault and referenced by the notebooks via Key Vault SDK or directly via `.env` for local development.

### `provision_azure.sh` Integration

The existing `scripts/provision_azure.sh` wraps the Bicep deployment:

```bash
#!/usr/bin/env bash
set -euo pipefail

ENV="${1:-dev}"
BICEP_DIR="infra/bicep"
PARAM_FILE="${BICEP_DIR}/env/${ENV}.bicepparam"

if [[ ! -f "${PARAM_FILE}" ]]; then
  echo "ERROR: Parameter file not found: ${PARAM_FILE}"
  echo "Available environments: dev, test, prod"
  exit 1
fi

echo "Deploying ${ENV} environment..."

# Validate
az deployment sub what-if \
  --location eastus2 \
  --template-file "${BICEP_DIR}/main.bicep" \
  --parameters "${PARAM_FILE}"

# Deploy
az deployment sub create \
  --name "sfai-${ENV}-$(date +%Y%m%d%H%M)" \
  --location eastus2 \
  --template-file "${BICEP_DIR}/main.bicep" \
  --parameters "${PARAM_FILE}" \
  --query 'properties.outputs' -o json > /tmp/deploy-outputs.json

# Write outputs to .env.azure
echo "# Azure outputs from Bicep deployment (${ENV})" > .env.azure
jq -r 'to_entries[] | "\(.key | ascii_upcase)=\(.value.value)"' /tmp/deploy-outputs.json >> .env.azure
echo "Azure outputs written to .env.azure — merge into .env"
```

---

## CI/CD Pipeline Design (GitHub Actions)

### Workflow: Infrastructure Deployment (`deploy-infra.yml`)

```yaml
name: Deploy Infrastructure
on:
  push:
    branches: [main]
    paths: ['infra/bicep/**']
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'dev'
        type: choice
        options: [dev, test, prod]

permissions:
  id-token: write    # OIDC for Azure login
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - name: Bicep lint
        run: az bicep lint --file infra/bicep/main.bicep
      - name: What-if (dev)
        run: |
          az deployment sub what-if \
            --location eastus2 \
            --template-file infra/bicep/main.bicep \
            --parameters infra/bicep/env/dev.bicepparam

  deploy-dev:
    needs: validate
    if: github.ref == 'refs/heads/main' || github.event.inputs.environment == 'dev'
    runs-on: ubuntu-latest
    environment: dev
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - name: Deploy dev
        run: |
          az deployment sub create \
            --name "sfai-dev-${{ github.run_number }}" \
            --location eastus2 \
            --template-file infra/bicep/main.bicep \
            --parameters infra/bicep/env/dev.bicepparam

  deploy-test:
    needs: deploy-dev
    if: github.event.inputs.environment == 'test' || github.event.inputs.environment == 'prod'
    runs-on: ubuntu-latest
    environment: test
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - name: Deploy test
        run: |
          az deployment sub create \
            --name "sfai-test-${{ github.run_number }}" \
            --location eastus2 \
            --template-file infra/bicep/main.bicep \
            --parameters infra/bicep/env/test.bicepparam

  deploy-prod:
    needs: deploy-test
    if: github.event.inputs.environment == 'prod'
    runs-on: ubuntu-latest
    environment:
      name: prod
      # Requires manual approval via GitHub environment protection rules
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - name: Deploy prod
        run: |
          az deployment sub create \
            --name "sfai-prod-${{ github.run_number }}" \
            --location eastus2 \
            --template-file infra/bicep/main.bicep \
            --parameters infra/bicep/env/prod.bicepparam
```

### Workflow: CI (`ci.yml`)

```yaml
name: CI
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt
      - name: Lint (ruff)
        run: ruff check .
      - name: Type check (mypy)
        run: mypy shared/ mcp_servers/
      - name: Unit tests
        run: pytest tests/unit/ -v
      - name: Contract tests
        run: pytest tests/contract/ -v

  bicep-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Bicep build (validate syntax)
        run: az bicep build --file infra/bicep/main.bicep --stdout > /dev/null
```

### GitHub Secrets & Environment Configuration

| Secret | Scope | Purpose |
|--------|-------|---------|
| `AZURE_CLIENT_ID` | Repository | Service principal / OIDC app registration |
| `AZURE_TENANT_ID` | Repository | Entra ID tenant |
| `AZURE_SUBSCRIPTION_ID` | Repository | Target subscription |

Each GitHub environment (`dev`, `test`, `prod`) can have:
- **Protection rules**: Required reviewers for `prod`
- **Environment secrets**: Override subscription/client IDs per environment if using separate subscriptions
- **Wait timer**: Optional delay before production deployment

---

## Automation & Setup

### Bootstrap Script (`scripts/bootstrap_env.sh`)

1. Check Python 3.11+ available
2. Create `.venv` virtual environment
3. Install `requirements.txt`
4. Copy `.env.example` → `.env` if not exists
5. Print checklist of required environment variables

### Provisioning Script (`scripts/provision_azure.sh`)

1. Accept environment name argument (default: `dev`)
2. Validate parameter file exists for target environment
3. Run `az deployment sub what-if` for preview
4. Run `az deployment sub create` with corresponding `.bicepparam` file
5. Capture deployment outputs
6. Write Azure-specific outputs to `.env.azure`

---

## Documentation Plan

| Document | Location | Content |
|----------|----------|---------|
| README.md | Root | Project overview, quickstart pointer, architecture diagram |
| quickstart.md | specs/001…/ | Step-by-step getting started (this plan's output) |
| salesforce-setup.md | docs/ | Connected App creation, OAuth scopes, IP allowlisting |
| azure-setup.md | docs/ | Manual Azure provisioning alternative, Bicep module reference, per-environment guidance |
| extending-scenarios.md | docs/ | How to add new MCP tools and notebooks |

---

## Phased Work Breakdown

> **Note**: This section provides a high-level overview of work phases
> for architectural context. The authoritative, task-level implementation
> plan is [`tasks.md`](tasks.md), which organizes work by user story
> with explicit dependencies and parallelism markers.

### Phase 1: Foundation (Week 1–2)

| # | Task | Depends On | Output |
|---|------|-----------|--------|
| 1.1 | Create project root structure, `pyproject.toml`, `requirements.txt` | — | Skeleton repo |
| 1.2 | Implement `shared/config.py` (env loader, `.env` parsing) | 1.1 | Config module |
| 1.3 | Implement `shared/models.py` (all Pydantic models from data-model.md) | 1.1 | Response models |
| 1.4 | Implement `shared/salesforce_client.py` (simple-salesforce wrapper, rate tracking) | 1.2, 1.3 | SF client |
| 1.5 | Implement `shared/auth.py` (OAuth flow helpers, token refresh) | 1.2 | Auth module |
| 1.6 | Write unit tests for models and config | 1.3, 1.2 | `tests/unit/` |
| 1.7 | Create `.env.example` template | 1.2 | Template file |
| 1.8 | Create `scripts/bootstrap_env.sh` | 1.1 | Bootstrap script |
| 1.9 | Create `config/risk_thresholds.yaml` | 1.1 | Risk config |
| 1.10 | Author `agents/sales/system_prompt.md` | 1.1 | Sales prompt |
| 1.11 | Author `agents/service/system_prompt.md` | 1.1 | Service prompt |
| 1.12 | **Bicep: `modules/storage.bicep`** | 1.1 | Storage IaC |
| 1.13 | **Bicep: `modules/keyvault.bicep`** | 1.12 | Key Vault IaC |
| 1.14 | **Bicep: `modules/app-insights.bicep`** | 1.1 | Observability IaC |
| 1.15 | **Bicep: `main.bicep`** (foundation modules only) | 1.12–1.14 | Bicep orchestrator |
| 1.16 | **Bicep: `env/dev.bicepparam`** | 1.15 | Dev parameters |
| 1.17 | **GitHub Actions: `ci.yml`** (lint + test + Bicep validate) | 1.1 | CI pipeline |

### Phase 2: MCP Servers (Week 3–4)

| # | Task | Depends On | Output |
|---|------|-----------|--------|
| 2.1 | Implement `mcp_servers/salesforce_crm/server.py` (FastMCP setup) | 1.4, 1.5 | CRM server |
| 2.2 | Implement account tools: `get_account`, `search_accounts` | 2.1 | Account tools |
| 2.3 | Implement contact tools: `get_contacts_for_account` | 2.1 | Contact tools |
| 2.4 | Implement opportunity tools: `get_opportunities`, `get_pipeline_summary` | 2.1, 1.9 | Opp tools |
| 2.5 | Implement case tools: `get_case`, `create_case`, `update_case` | 2.1 | Case tools |
| 2.6 | Implement activity tools: `get_recent_activities`, `create_task` | 2.1 | Activity tools |
| 2.7 | Implement lead tools: `get_leads`, `update_lead_status` | 2.1 | Lead tools |
| 2.8 | Implement user tools: `get_team_members` | 2.1 | User tools |
| 2.9 | Implement `mcp_servers/salesforce_knowledge/server.py` | 1.4 | KB server |
| 2.10 | Implement `search_articles` (SOSL + SOQL fallback) | 2.9 | KB search tool |
| 2.11 | Implement `get_article_by_id` | 2.9 | KB article tool |
| 2.12 | Write contract tests for all CRM tools | 2.2–2.8 | `tests/contract/` |
| 2.13 | Write contract tests for knowledge tools | 2.10, 2.11 | `tests/contract/` |
| 2.14 | **Bicep: `modules/ai-foundry.bicep`** | 1.15 | AI Foundry IaC |
| 2.15 | **Bicep: `modules/openai.bicep`** | 2.14 | OpenAI IaC |
| 2.16 | **Bicep: `modules/ai-search.bicep`** | 1.12 | AI Search IaC |
| 2.17 | **Update `main.bicep`**: add AI Foundry + OpenAI + AI Search modules | 2.14–2.16 | Full IaC |
| 2.18 | **Bicep: `env/test.bicepparam` + `env/prod.bicepparam`** | 2.17 | All env params |
| 2.19 | **GitHub Actions: `deploy-infra.yml`** | 2.17 | Infra CD pipeline |

### Phase 3: Agent Integration (Week 5–6)

| # | Task | Depends On | Output |
|---|------|-----------|--------|
| 3.1 | Implement Notebook 1: Sales Pipeline Summary | 2.4, 2.8, 1.10 | Notebook 1 |
| 3.2 | Implement Notebook 2: Account Meeting Briefing | 2.2, 2.3, 2.6, 1.10 | Notebook 2 |
| 3.3 | Implement Notebook 3: Case Triage | 2.5, 2.10, 2.11, 1.11 | Notebook 3 |
| 3.4 | Implement Notebook 4: Knowledge Base Assistant | 2.10, 2.11, 1.11 | Notebook 4 |
| 3.5 | Test multi-turn conversation flow in all notebooks | 3.1–3.4 | Validated notebooks |
| 3.6 | Implement write-back confirmation protocol (create_case, update_case, etc.) | 3.3 | Confirmation UX |
| 3.7 | Write integration tests (`tests/integration/test_agent_e2e.py`) | 3.1–3.4 | E2E tests |
| 3.8 | **Bicep: `modules/app-service.bicep`** (hosted MCP/SSE) | 2.17 | App Service IaC |
| 3.9 | **Update `main.bicep`**: add App Service module (conditional) | 3.8 | Complete IaC |
| 3.10 | **Provision test environment** via `deploy-infra.yml` | 3.9, 2.19 | Test Azure resources |
| 3.11 | **Update `provision_azure.sh`**: Bicep + output capture | 3.9 | Updated script |

### Phase 4: Polish & Documentation (Week 7–8)

| # | Task | Depends On | Output |
|---|------|-----------|--------|
| 4.1 | Write `docs/salesforce-setup.md` | 1.5 | SF setup guide |
| 4.2 | Write `docs/azure-setup.md` (with Bicep module reference) | 3.9 | Azure guide |
| 4.3 | Write `docs/extending-scenarios.md` | 2.1–2.11 | Extension guide |
| 4.4 | Write root `README.md` with architecture diagram | All | README |
| 4.5 | Add Application Insights telemetry to MCP servers | 1.14, 2.1 | Instrumented servers |
| 4.6 | Edge-case hardening: disambiguation, rate limits, auth errors | 2.1–2.11 | Robust error handling |
| 4.7 | Final review: all notebooks run end-to-end against real org | All | Validated demo |
| 4.8 | **Provision prod environment** (manual approval gate) | 4.7, 3.9 | Prod Azure resources |
| 4.9 | **Security review**: Key Vault access policies, RBAC, network rules | 4.8 | Security sign-off |

**Total**: 49 tasks across 4 phases (8 weeks). IaC tasks are integrated into each phase alongside the application code they support.

---

## Constitution Check (Post-Design)

*Re-evaluation after Phase 1 design completion (data-model, contracts, IaC strategy).*

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| I | Integration-First Architecture | ✅ PASS | All 15 MCP tools have JSON Schema contracts. Bicep modules expose typed parameters and outputs. Each module declares dependencies explicitly. `.bicepparam` files are the single source of environment configuration. |
| II | Security & Compliance by Default | ✅ PASS | Key Vault with HSM (prod) for secrets. Per-user OAuth enforces FLS/sharing. OIDC for GitHub Actions → Azure auth (no stored credentials). `@secure()` decorator on all sensitive Bicep parameters. Storage ZRS in prod. |
| III | AI-Responsible & Human-in-the-Loop | ✅ PASS | Write-back tools require explicit confirmation. Azure AI Content Safety enabled at platform level. System prompts enforce citation requirements. All AI actions auditable via Application Insights. |
| IV | Iterative Delivery & Phased Rollout | ✅ PASS | 4-phase plan with IaC tasks integrated per phase. Dev environment in Phase 1; test in Phase 3; prod in Phase 4 (with manual approval gate). GitHub Actions enforces progressive deployment (dev → test → prod). |
| V | Operational Excellence & Observability | ✅ PASS | Application Insights provisioned via Bicep module. Log Analytics workspace for diagnostics. CI pipeline validates Bicep syntax. `deploy-infra.yml` includes what-if validation before deployment. Per-session API rate tracking in application code. |

**Gate result**: PASS — all principles satisfied post-design. Proceed to Phase 2 (task generation via `/speckit.tasks`).
