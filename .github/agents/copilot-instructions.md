# salesforce-foundryagent Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-16

## Active Technologies

- **Language**: Python 3.11+
- **Agent SDK**: `azure-ai-projects`, `azure-identity`
- **MCP**: `mcp[cli]`, `fastmcp`
- **Salesforce**: `simple-salesforce` (REST API v62.0)
- **Data/HTTP**: `pydantic`, `httpx`, `python-dotenv`
- **Testing**: `pytest`, `pytest-asyncio`
- **Linting**: `ruff`
- **IaC**: Bicep (modular, `.bicepparam` per environment)
- **Storage**: Salesforce (system of record), Azure AI Search (KB RAG)

## Project Structure

```text
salesforce-foundryagent/
├── agents/                  # Agent system prompts (sales/, service/)
├── mcp_servers/
│   ├── salesforce_crm/      # FastMCP server — 13 CRM tools
│   └── salesforce_knowledge/ # FastMCP server — 2 Knowledge tools
├── shared/                  # Common modules (models, auth, config, SF client)
├── notebooks/               # Scenario demo notebooks (01–05)
├── scripts/                 # bootstrap_env.sh, provision_azure.sh, deploy_app.sh
├── infra/bicep/             # main.bicep + modules/ + env/ (.bicepparam)
├── config/                  # risk_thresholds.yaml
├── docs/                    # Setup guides, runbooks
├── tests/                   # unit/, contract/, integration/, performance/
└── specs/                   # Feature specs, plans, contracts, tasks
```

## Commands

```bash
# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run tests
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/contract/

# Lint
ruff check .

# Provision Azure infrastructure
./scripts/provision_azure.sh dev

# Bootstrap local environment
./scripts/bootstrap_env.sh
```

## Code Style

- Python 3.11+: Follow standard conventions, type hints required
- Pydantic models for all data structures (`shared/models.py`)
- Async patterns for MCP tool implementations
- Salesforce access exclusively through `shared/salesforce_client.py`
- Environment config via `shared/config.py` (reads from `.env` / env vars)

## Hosting Modes

Runtime components support configurable hosting via `hostingMode` parameter in `.bicepparam`:

| Mode | Description |
|------|-------------|
| `none` | No hosted compute — notebooks only |
| `appService` | Azure App Service (PaaS, Linux, zip deploy) |
| `aca` | Azure Container Apps (container-based, ACR + Docker) |

## Key Conventions

- MCP tool contracts are defined in `specs/001-salesforce-ai-assistant/contracts/`
- All Salesforce writes require explicit user confirmation (FR-007)
- Per-user OAuth 2.0 delegated auth — no service-account shortcuts
- Bicep modules are independently deployable; `main.bicep` orchestrates
- Feature spec lives in `specs/001-salesforce-ai-assistant/`

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
