# Salesforce AI Assistant

An AI-powered assistant for Salesforce CRM built on **Azure AI Foundry Agent Framework** with **Model Context Protocol (MCP)** for tool integration. Enables Account Executives, Sales Managers, and Customer Service Representatives to interact with Salesforce data using natural language.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Azure AI Foundry                       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │  Sales Agent  │  │Service Agent │  │  Orchestrator │ │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘ │
│         │                  │                   │         │
│  ┌──────▼──────────────────▼───────────────────▼──────┐ │
│  │            Azure AI Agent Service (GPT-4o)         │ │
│  └──────────────────────┬─────────────────────────────┘ │
└─────────────────────────┼───────────────────────────────┘
                          │ MCP (stdio/SSE)
              ┌───────────┴───────────┐
              │                       │
    ┌─────────▼──────────┐  ┌────────▼───────────┐
    │  salesforce-crm    │  │salesforce-knowledge │
    │  MCP Server        │  │  MCP Server         │
    │  (15 tools)        │  │  (2 tools)          │
    └─────────┬──────────┘  └────────┬───────────┘
              │                       │
              └───────────┬───────────┘
                          │ REST API v62.0
                 ┌────────▼────────┐
                 │   Salesforce    │
                 │   CRM + KB     │
                 └────────────────┘
```

## Features

| User Story | Persona | Description |
|------------|---------|-------------|
| US1 | Account Executive | Meeting preparation briefings with account, contacts, opportunities, activities |
| US2 | Sales Manager | Pipeline summary with at-risk deal flagging |
| US3 | CSR | Case triage with KB-grounded response drafts |
| US4 | Any User | Natural-language CRM/KB queries |
| US5 | Account Executive | Next Best Action recommendations |
| US6 | Support Manager | Case queue monitoring with SLA indicators |
| US7 | Cross-functional | Multi-domain orchestrator for unified insights |

## Quick Start

### Prerequisites

- Python 3.11+
- Azure subscription with Azure AI Foundry access
- Salesforce org with Connected App configured

### Setup

```bash
# Clone and bootstrap
git clone <repo-url>
cd salesforce-foundryagent
./scripts/bootstrap_env.sh

# Configure environment
cp .env.example .env
# Edit .env with your Azure + Salesforce credentials

# Run linting and tests
source .venv/bin/activate
ruff check .
pytest tests/
```

### Run a Notebook

```bash
# Activate the virtual environment
source .venv/bin/activate

# Launch Jupyter
jupyter notebook notebooks/
```

Start with [`02_sales_account_briefing.ipynb`](notebooks/02_sales_account_briefing.ipynb) for a quick demo.

## Project Structure

```
├── Dockerfile                  # Multi-stage Docker build (CRM + Knowledge targets)
├── agents/                     # Agent system prompts
│   ├── sales/system_prompt.md
│   └── service/system_prompt.md
├── config/                     # Configuration files
│   └── risk_thresholds.yaml
├── docs/                       # Documentation
│   ├── azure-setup.md
│   ├── data-classification.md
│   ├── extending-scenarios.md
│   ├── hosting-modes.md        # App Service vs Container Apps comparison
│   ├── post-pilot-survey.md
│   ├── salesforce-quickstart.md # Salesforce setup & credential onboarding guide
│   └── runbooks/               # Operational runbooks
├── infra/bicep/                # Azure Infrastructure as Code
│   ├── main.bicep              # Orchestrator with hostingMode param
│   ├── env/                    # Per-environment parameters
│   └── modules/                # Modular Bicep resources
│       ├── ai-foundry.bicep
│       ├── ai-search.bicep
│       ├── app-insights.bicep
│       ├── app-service.bicep
│       ├── bot-service.bicep
│       ├── container-apps.bicep    # ACA Environment + Container Apps
│       ├── container-registry.bicep # ACR for Docker images
│       ├── keyvault.bicep
│       ├── monitor-alerts.bicep
│       ├── openai.bicep
│       └── storage.bicep
├── mcp_servers/                # MCP Server implementations
│   ├── salesforce_crm/         # 15 CRM tools
│   └── salesforce_knowledge/   # 2 Knowledge tools
├── notebooks/                  # Jupyter notebooks (one per user story)
├── shared/                     # Shared utilities
│   ├── config.py
│   ├── models.py
│   ├── auth.py
│   ├── salesforce_client.py
│   └── knowledge_sync.py
├── tests/                      # Test suite
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   └── performance/
└── scripts/                    # Automation scripts
    ├── bootstrap_env.sh
    ├── deploy_app.sh           # Unified deploy (App Service or ACA)
    └── provision_azure.sh
```

## MCP Tools

### salesforce-crm (15 tools)

| Tool | Object | Description |
|------|--------|-------------|
| `get_account` | Account | Lookup by ID or name |
| `search_accounts` | Account | Search with filters |
| `get_contacts_for_account` | Contact | Contacts with role enrichment |
| `get_opportunities` | Opportunity | List with filters |
| `get_pipeline_summary` | Opportunity | Aggregated pipeline view |
| `get_deal_activity_gaps` | Opportunity | NBA activity gap analysis |
| `get_recent_activities` | Task/Event | Merged activity timeline |
| `create_task` | Task | Create with write-back confirmation |
| `get_case` | Case | Lookup by ID or number |
| `create_case` | Case | Create with write-back confirmation |
| `update_case` | Case | Update with write-back confirmation |
| `get_case_queue_summary` | Case | Queue status aggregation |
| `get_leads` | Lead | List leads with filters |
| `update_lead_status` | Lead | Update with write-back confirmation |
| `get_team_members` | User | Team member lookup |

### salesforce-knowledge (2 tools)

| Tool | Description |
|------|-------------|
| `search_articles` | Full-text search (SOSL + SOQL fallback) |
| `get_article_by_id` | Full article content with HTML stripping |

## Infrastructure

Deploys to Azure using Bicep IaC with three environments. Hosting mode is configurable via the `hostingMode` parameter (`none`, `appService`, or `aca`). See [docs/hosting-modes.md](docs/hosting-modes.md) for a detailed comparison.

| Resource | Dev | Test | Prod |
|----------|-----|------|------|
| AI Foundry (Hub + Project) | ✅ | ✅ | ✅ |
| OpenAI (GPT-4o) | 10K TPM | 30K TPM | 80K TPM |
| AI Search | Free | Basic | Standard |
| Storage | LRS | ZRS | GRS |
| Key Vault | Standard | Standard | Standard |
| App Insights | Auto (ACA) | ✅ | ✅ |
| Hosting Mode | aca | aca | aca |
| Container Apps (ACA) | ✅ | ✅ | ✅ |
| Container Registry | Basic | Basic | Standard |

> App Service hosting is also available by setting `hostingMode` to `appService`. See [docs/hosting-modes.md](docs/hosting-modes.md).

### Azure Deployment (ACA)

When using `hostingMode=aca`, MCP servers run as containerized apps on Azure Container Apps.
Initial provisioning uses a placeholder image; real images are deployed in a second step.

```bash
# 1. Provision Azure infrastructure (creates ACA with placeholder image)
./scripts/provision_azure.sh dev

# 2. Assign Key Vault Secrets Officer role to your user
USER_OID=$(az ad signed-in-user show --query id -o tsv)
az role assignment create \
  --role "Key Vault Secrets Officer" \
  --assignee-object-id "$USER_OID" \
  --assignee-principal-type User \
  --scope "$(az keyvault show --name <vault-name> --query id -o tsv)"

# 3. Store Salesforce credentials in Key Vault
az keyvault secret set --vault-name <vault-name> --name sf-client-id --value '<key>'
az keyvault secret set --vault-name <vault-name> --name sf-client-secret --value '<secret>'
az keyvault secret set --vault-name <vault-name> --name sf-instance-url --value '<url>'
az keyvault secret set --vault-name <vault-name> --name sf-access-token --value '<token>'

# 4. Build linux/amd64 images, push to ACR, and update Container Apps
./scripts/deploy_app.sh dev aca
```

#### Local Docker Testing

```bash
# Build and run locally (uses native ARM64 on Apple Silicon)
docker build --target crm-server -t sfai-crm:latest .
docker build --target knowledge-server -t sfai-knowledge:latest .
docker run -d -p 8000:8000 --env-file .env sfai-crm:latest
docker run -d -p 8001:8000 --env-file .env sfai-knowledge:latest
curl http://localhost:8000/health  # {"status":"ok"}
```

## Security

- **OAuth 2.0** per-user delegated authentication
- **FLS/Sharing rules** enforced natively by Salesforce
- **Write-back confirmation** required for all data modifications
- **OIDC** for CI/CD (no stored credentials)
- **Key Vault** for secret management
- **RBAC** across all Azure resources

## Contributing

1. Read [docs/extending-scenarios.md](docs/extending-scenarios.md) for adding tools/agents
2. Follow the contract-first approach: define schemas before implementation
3. Write contract tests for all new MCP tools
4. Run `ruff check .` and `pytest` before submitting PRs

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
