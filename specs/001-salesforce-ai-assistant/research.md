# Research: Salesforce AI Assistant

**Date**: 2026-02-16 | **Phase**: 0 (Outline & Research)
**Purpose**: Resolve all NEEDS CLARIFICATION items from Technical Context and document technology decisions.

---

## 1. Agent Framework + MCP Integration

### Decision: Use Azure AI Foundry Agent Framework with `azure-ai-projects` SDK

**Rationale**: Managed service with native MCP support, enterprise security controls (VNET, managed identity, content safety), and a simple programming model (create agent → register tools → run conversation). The SDK mirrors the OpenAI Assistants API pattern but runs entirely on Azure.

**Alternatives Considered**:
- **Semantic Kernel**: Open-source orchestration SDK. More flexible but requires more boilerplate. Agent Framework is a managed service with built-in MCP support — less operational overhead.
- **LangChain/LangGraph**: Popular OSS frameworks. Not chosen because the project requirement specifies Microsoft Agent Framework as the approved standard.
- **AutoGen**: Microsoft Research's multi-agent framework. Better suited for agent-to-agent autonomous conversations; Agent Framework better fits our tool-calling + human-in-the-loop pattern.

### Agent Creation Pattern

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

client = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint="https://<project>.services.ai.azure.com/api",
)

agent = client.agents.create_agent(
    model="gpt-4o",
    name="Sales Agent",
    instructions=system_prompt,
    toolset=toolset,  # MCP tool connections
)

thread = client.agents.create_thread()
client.agents.create_message(thread_id=thread.id, role="user", content=user_input)
run = client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
messages = client.agents.list_messages(thread_id=thread.id)
```

### MCP Tool Registration

```python
from azure.ai.projects.models import McpToolConnection, McpStdioServerParameters

connection = McpToolConnection(
    server_label="salesforce-crm",
    server_parameters=McpStdioServerParameters(
        command="python",
        args=["mcp_servers/salesforce_crm/server.py"],
        env={"SF_ACCESS_TOKEN": token, "SF_INSTANCE_URL": url},
    ),
)

toolset = ToolSet()
toolset.add(connection)
```

### Key SDK Classes

| Class | Purpose |
|-------|---------|
| `AIProjectClient` | Entry point for agent management |
| `Agent` | Created agent with model, instructions, tools |
| `AgentThread` | Conversation session container |
| `ToolSet` | Collection of tool connections |
| `McpToolConnection` | MCP server connection wrapper |
| `McpStdioServerParameters` | Config for stdio transport |
| `McpSseServerParameters` | Config for SSE transport |

---

## 2. MCP Transport Strategy

### Decision: stdio for notebooks, SSE/Streamable HTTP for hosted deployment

**Rationale**: stdio requires zero network configuration — Agent Framework spawns the MCP server as a subprocess. Ideal for notebook scenarios. SSE is required for production when multiple agents share a server or when the server runs in a separate container.

**Transport Comparison**:

| Transport | Use Case | Pros | Cons |
|-----------|----------|------|------|
| stdio | Notebooks, local dev | Zero config; subprocess lifecycle | Single-machine only |
| SSE | Production, shared servers | Network-accessible; scalable | Requires HTTP hosting + TLS |
| Streamable HTTP | Emerging standard | Stateless requests; HTTP-native | Newer, less battle-tested |

**Alternatives Considered**:
- **SSE everywhere**: Would add unnecessary network complexity to notebook demos.
- **Streamable HTTP for notebooks**: Not enough SDK maturity as of early 2026; stdio is simpler and proven.

---

## 3. Salesforce REST API Access

### Decision: Use `simple-salesforce` Python library with REST API v62.0

**Rationale**: Thin wrapper that handles auth header injection, automatic pagination (`query_all()`), SOQL/SOSL queries, and CRUD operations. Widely adopted and well-maintained.

**API Version**: v62.0 (Winter '26). Base URL: `https://<instance>.my.salesforce.com/services/data/v62.0/`

**Key API Patterns**:

```python
from simple_salesforce import Salesforce

sf = Salesforce(instance_url=url, session_id=token, version='62.0')

# SOQL query
results = sf.query("SELECT Id, Name FROM Account LIMIT 25")

# Create record
sf.Case.create({'Subject': '...', 'Priority': 'High'})

# Update record
sf.Case.update('500XXX', {'Status': 'Working'})

# Full-text search (SOSL)
results = sf.search("FIND {keyword} RETURNING KnowledgeArticleVersion(Id, Title)")
```

**Alternatives Considered**:
- **Salesforce GraphQL API**: Limited object support, less mature for CRM objects.
- **Salesforce Bulk API 2.0**: Optimized for >10K records; our queries return <50 records.
- **Raw `httpx`/`requests`**: Would require reimplementing auth, pagination, error handling.

---

## 4. Salesforce Authentication

### Decision: Per-user delegated OAuth 2.0 Authorization Code flow

**Rationale**: Each user's API calls execute under their Salesforce profile. Field-level security (FLS), sharing rules, and record-level access are **natively enforced** — the AI assistant never exposes data a user isn't permitted to see. This satisfies Constitution Principle II (Security & Compliance by Default) without custom permission logic.

**Flow**:
1. User authorizes via Salesforce OAuth consent screen
2. App receives authorization code at callback URL
3. Exchange code for access_token + refresh_token
4. Pass access_token to MCP server via env var (stdio) or header (SSE)
5. Refresh token when access_token expires (~2 hours)

**Connected App Configuration**:
- Callback URL: `https://localhost:8443/callback` (dev) or app redirect URI (prod)
- OAuth Scopes: `api`, `refresh_token`, `openid`
- Consumer Key + Consumer Secret stored in Azure Key Vault

**Alternatives Considered**:
- **Service Account / JWT Bearer** — Single integration user identity. Rejected because it bypasses FLS/sharing rules; would require implementing permission checks in application code.
- **Client Credentials flow** — Machine-to-machine auth. Same problem as service account — runs under a single identity.

---

## 5. API Rate Limits

### Decision: Track API usage per session, warn at 80% of per-minute threshold

**Finding**: Salesforce daily API call limits for target editions:

| Edition | Base Daily Limit | Per-License Add-on |
|---------|------------------|--------------------|
| Enterprise | 100,000 calls/24hr | +1,000 per user license |
| Unlimited | 1,000,000 calls/24hr | +5,000 per user license |

**Project Impact** (demo scenario): 50 users × 20 queries/day × 5 calls/query = ~5,000 calls/day — well within limits.

**Additional Limits**:
- Concurrent API requests: 25 per user
- Query result size: 2,000 records per SOQL query
- API request body: 6MB max

**Implementation**: `shared/salesforce_client.py` maintains a per-session API call counter. When a session's count exceeds 80% of the per-minute estimate, the wrapper returns a structured warning that the agent relays to the user (FR-014).

---

## 6. FastMCP Tool Definition Patterns

### Decision: Use FastMCP decorator-based pattern with Pydantic models for complex inputs

**Rationale**: FastMCP auto-generates JSON Schema from Python type annotations and Pydantic models. The decorator pattern is concise and the docstrings become tool descriptions that guide the LLM.

**Example**:

```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional

mcp = FastMCP("salesforce-crm")

@mcp.tool()
async def get_account(account_name: str) -> dict:
    """Retrieve account details by name from Salesforce."""
    ...

class CaseUpdateInput(BaseModel):
    case_id: str = Field(description="Salesforce Case ID")
    priority: Optional[str] = Field(None, description="New priority")

@mcp.tool()
async def update_case(input: CaseUpdateInput) -> dict:
    """Update a Salesforce case."""
    ...

if __name__ == "__main__":
    mcp.run(transport="stdio")  # or "sse"
```

**Auth Context Passing**:
- stdio: Environment variables (`SF_ACCESS_TOKEN`, `SF_INSTANCE_URL`)
- SSE: HTTP headers (`X-SF-Access-Token`) extracted from request context

---

## 7. Azure Resources Required

### Decision: Azure AI Foundry Hub + Project with supporting services

| Resource | Purpose | SKU/Tier |
|----------|---------|----------|
| Azure AI Foundry Hub | Container for projects | Standard |
| Azure AI Foundry Project | Agent hosting | Standard |
| Azure OpenAI Service | GPT-4o model host | Standard S0 |
| GPT-4o Deployment | Agent model | GlobalStandard |
| Azure AI Search | KB article index (RAG) | Basic |
| Azure Key Vault | Salesforce OAuth secrets | Standard |
| Application Insights | Telemetry and logging | Standard |
| Azure Storage Account | AI Foundry file storage | Standard LRS |

**Provisioning**: Bicep templates in `infra/main.bicep`, wrapped by `scripts/provision_azure.sh`.

---

## 8. Content Safety

### Decision: Azure AI Content Safety at platform level (no code changes)

**Rationale**: Azure AI Content Safety is enforced transparently on all Azure OpenAI deployments. Default content filters cover hate, self-harm, sexual content, and violence. Custom filter policies can be created in the AI Foundry portal and applied to the GPT-4o deployment. This aligns with Constitution Principle III (AI-Responsible & Human-in-the-Loop).

**Additionally**: AI Foundry's groundedness detection can flag responses not grounded in tool-provided data — relevant for our citation requirement (FR-011).

---

## 9. SOQL Query Patterns for Key Objects

### Decision: Standardized SOQL patterns with bounded results (LIMIT clause)

Documented query patterns for all 12 Salesforce objects used by MCP tools:

| Object | Primary Query Pattern | Max Results |
|--------|----------------------|-------------|
| Account | `SELECT ... FROM Account WHERE Name LIKE '%{query}%' LIMIT 25` | 25 |
| Contact | `SELECT ... FROM Contact WHERE AccountId = '{id}' LIMIT 25` | 25 |
| Lead | `SELECT ... FROM Lead WHERE Status = '{status}' AND OwnerId = '{id}' LIMIT 25` | 25 |
| Opportunity | `SELECT ... FROM Opportunity WHERE IsClosed = false AND OwnerId IN (...) LIMIT 50` | 50 |
| Case | `SELECT ... FROM Case WHERE Status != 'Closed' LIMIT 25` | 25 |
| CaseComment | Subquery on Case: `(SELECT ... FROM CaseComments LIMIT 5)` | 5 |
| KnowledgeArticleVersion | SOQL for structured search; SOSL for full-text | 10 |
| Task | `SELECT ... FROM Task WHERE WhatId = '{id}' AND CreatedDate = LAST_N_DAYS:30 LIMIT 25` | 25 |
| Event | `SELECT ... FROM Event WHERE WhatId = '{id}' LIMIT 25` | 25 |
| User | `SELECT ... FROM User WHERE ManagerId = '{id}'` | 50 |
| OpportunityContactRole | Subquery via Contact relationship | N/A |
| OpportunityLineItem | Subquery via Opportunity relationship | N/A |

**Cross-object queries**: SOQL supports relationship queries (parent-to-child subqueries, child-to-parent dot notation) but not arbitrary JOINs. Queries needing cross-object correlation (e.g., "accounts with open deals AND open cases") require two queries with client-side merging.

---

## 10. Infrastructure as Code (Bicep)

### Decision: Modular Bicep with `.bicepparam` files per environment

**Rationale**: Bicep is the native Azure IaC language — first-class support in Azure CLI, VS Code, and GitHub Actions. Modular structure (one file per resource type) enables independent iteration, clear dependency graphs, and reuse. `.bicepparam` files (not JSON) are the recommended parameter format per Bicep best practices, providing type safety and `using` references that link each param file to its template.

**Alternatives Considered**:
- **Terraform**: Multi-cloud IaC. Not chosen because the project is Azure-only, and Bicep provides tighter integration (ARM native, zero provider config, same-day API support for new Azure resources).
- **Azure Developer CLI (azd)**: Higher-level abstraction. Not chosen because it adds opinionated project structure that conflicts with our existing layout. Bicep gives full control.
- **ARM Templates (JSON)**: Predecessor to Bicep. Rejected — significantly more verbose, no module system, no `.bicepparam` support.
- **Pulumi**: Code-first IaC in Python. Interesting but adds another runtime dependency and learning curve for the team.

### Module Strategy

Each Bicep module encapsulates a single Azure resource type with:
- Typed `param` declarations (no open `object` or `array` where avoidable)
- `@description()` decorators on non-obvious parameters
- `@secure()` decorator on all sensitive values
- Typed `output` declarations consumed by dependent modules or `main.bicep` outputs
- Resource symbolic names (no `resourceId()` function calls)
- `parent` property for child resources (no `/` in `name`)

### Azure Verified Modules (AVM)

Where applicable, modules follow Azure Verified Module patterns for naming, tagging, and diagnostic settings. Key AVM references:
- `Microsoft.CognitiveServices/accounts` — for OpenAI Service
- `Microsoft.KeyVault/vaults` — for Key Vault with RBAC or access policies
- `Microsoft.Search/searchServices` — for AI Search
- `Microsoft.MachineLearningServices/workspaces` — for AI Foundry Hub/Project (workspace kind: `hub` / `project`)

### Environment Strategy

| Environment | `.bicepparam` File | SKU Tier | Optional Resources |
|-------------|-------------------|----------|-------------------|
| **Dev** | `env/dev.bicepparam` | Minimal (Free AI Search, Standard KV, 10K TPM) | App Insights off, App Service off |
| **Test** | `env/test.bicepparam` | Mid (Basic AI Search, Standard KV, 30K TPM) | App Insights on, App Service on (B1) |
| **Prod** | `env/prod.bicepparam` | Production (Standard AI Search, Premium KV/HSM, 80K TPM, ZRS) | All on, App Service S1 |

### CI/CD Integration

- **GitHub Actions OIDC**: Federated identity — no stored Azure credentials in GitHub Secrets.
- **`deploy-infra.yml`**: Validates (lint + what-if) → deploys dev → deploys test → deploys prod (with manual approval).
- **`ci.yml`**: Runs `az bicep build` on every PR to catch syntax errors early.
- **Progressive deployment**: Dev auto-deploys on push to `main`; test and prod require explicit `workflow_dispatch` selection.

---

## Summary: All NEEDS CLARIFICATION Resolved

| Item | Resolution |
|------|------------|
| Language/Version | Python 3.11+ |
| Primary Dependencies | `azure-ai-projects`, `simple-salesforce`, `mcp`, `pydantic`, `httpx` |
| Storage | N/A — Salesforce is system of record; Azure AI Search for KB RAG |
| Testing | `pytest` + `pytest-asyncio` |
| Target Platform | Azure AI Foundry (cloud); notebooks local or Azure ML Compute |
| Performance Goals | Simple queries < 5s, complex < 15s (P95) |
| Constraints | < 50 concurrent users; SF API daily limits; Azure OpenAI token limits |
| Scale | < 500 total users (demo-first) |
| MCP transport | stdio (notebooks) / SSE (hosted) |
| SF auth model | Per-user delegated OAuth 2.0 |
| Content safety | Platform-level Azure AI Content Safety |
| Rate limiting | Per-session tracking in salesforce_client.py wrapper |
| Infrastructure | Bicep IaC, modular modules, `.bicepparam` per env, GitHub Actions CI/CD |
