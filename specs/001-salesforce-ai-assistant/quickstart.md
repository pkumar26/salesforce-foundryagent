# Quickstart: Salesforce AI Assistant

Get the Sales & Service AI Assistants running in under 15 minutes.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| **Python** | 3.11 or later |
| **Azure CLI** | Logged in (`az login`) with active subscription; Bicep CLI included (verify: `az bicep version`) |
| **Azure subscription** | With permissions to create AI Foundry, OpenAI, Key Vault, AI Search, Storage |
| **GitHub repo access** | Push access to `main` branch (triggers dev deployment via CI/CD) |
| **Salesforce org** | Enterprise or Unlimited Edition with API access |
| **Salesforce admin** | Completed Connected App setup (see [salesforce-setup.md](../../docs/salesforce-setup.md)) |
| **Git** | For cloning the repo |

---

## Step 1: Clone and Bootstrap

```bash
# Clone the repository
git clone <repo-url> salesforce-foundryagent
cd salesforce-foundryagent

# Run bootstrap script (creates venv, installs deps, copies .env template)
chmod +x scripts/bootstrap_env.sh
./scripts/bootstrap_env.sh

# Activate the virtual environment
source .venv/bin/activate
```

The bootstrap script will:
1. Create a Python 3.11+ virtual environment in `.venv/`
2. Install all dependencies from `requirements.txt`
3. Copy `.env.example` to `.env` if it doesn't exist
4. Print a checklist of required environment variables

---

## Step 2: Configure Salesforce Connected App

> **Prerequisite**: A Salesforce admin must have completed the Connected App setup.
> See [docs/salesforce-setup.md](../../docs/salesforce-setup.md) for detailed instructions.

You need these values from your Connected App:

| Variable | Where to find it |
|----------|-----------------|
| `SF_CONSUMER_KEY` | Connected App → Consumer Key |
| `SF_CONSUMER_SECRET` | Connected App → Consumer Secret |
| `SF_INSTANCE_URL` | Your Salesforce My Domain URL (e.g., `https://mycompany.my.salesforce.com`) |
| `SF_CALLBACK_URL` | The callback URL configured in the Connected App |

For demo/development, you can also use a pre-obtained access token:

| Variable | How to obtain |
|----------|--------------|
| `SF_ACCESS_TOKEN` | Via OAuth flow or Salesforce CLI: `sf org display --target-org <alias> --json` |
| `SF_INSTANCE_URL` | From the OAuth response or `sf org display` output |

---

## Step 3: Provision Azure Resources (Bicep IaC)

All Azure resources are managed as Infrastructure as Code using **Bicep** templates in `infra/bicep/`.

### Option A: Automated provisioning script (recommended)

```bash
# Provision the dev environment (default)
chmod +x scripts/provision_azure.sh
./scripts/provision_azure.sh dev

# Provision test or prod
./scripts/provision_azure.sh test
./scripts/provision_azure.sh prod
```

The script runs `az deployment sub create` with the matching `.bicepparam` file:

| Environment | Parameter File | Key Differences |
|-------------|---------------|------------------|
| `dev` | `infra/bicep/env/dev.bicepparam` | Free AI Search, 10K TPM, no App Service, LRS storage |
| `test` | `infra/bicep/env/test.bicepparam` | Basic AI Search, 30K TPM, optional App Service, LRS |
| `prod` | `infra/bicep/env/prod.bicepparam` | Standard AI Search, 80K TPM, App Service, ZRS storage |

### Option B: Direct Bicep deployment

```bash
# Deploy dev environment directly
az deployment sub create \
  --location eastus2 \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/env/dev.bicepparam

# Capture outputs for .env configuration
az deployment sub show \
  --name main \
  --query properties.outputs \
  --output json > /tmp/azure-outputs.json
```

### Option C: CI/CD (GitHub Actions)

Push to `main` automatically deploys the `dev` environment. For test/prod, use the `deploy-infra.yml` workflow dispatch in GitHub Actions.

### Resources provisioned

| Resource | Module | Mandatory | Notes |
|----------|--------|-----------|-------|
| Storage Account | `storage.bicep` | All envs | AI Foundry dependency |
| Key Vault | `keyvault.bicep` | All envs | Salesforce OAuth secrets |
| AI Foundry Hub + Project | `ai-foundry.bicep` | All envs | Agent hosting |
| Azure OpenAI (GPT-4o) | `openai.bicep` | All envs | Conversation model |
| AI Search | `ai-search.bicep` | All envs | Knowledge article RAG |
| Application Insights | `app-insights.bicep` | test, prod | Telemetry (optional in dev) |
| App Service | `app-service.bicep` | prod only | Hosted MCP servers (optional in test) |

After provisioning, the script prints output values for `.env` configuration.

---

## Step 4: Configure Environment

Edit `.env` with your values:

```bash
# Azure AI Foundry
# Azure AI Foundry (from Bicep deployment outputs)
AZURE_AI_PROJECT_ENDPOINT=https://<project>.services.ai.azure.com/api
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_KEY_VAULT_URI=https://kv-sfai-dev.vault.azure.net/

# Salesforce OAuth
SF_CONSUMER_KEY=<your-connected-app-consumer-key>
SF_CONSUMER_SECRET=<your-connected-app-consumer-secret>
SF_INSTANCE_URL=https://mycompany.my.salesforce.com
SF_CALLBACK_URL=https://localhost:8443/callback

# OR: Direct access token (for development/demo only)
SF_ACCESS_TOKEN=<your-access-token>

# Optional: Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=<from-azure-provisioning>
```

---

## Step 5: Run a Notebook

Each notebook is a self-contained scenario. Start with the pipeline summary:

```bash
# Option A: Jupyter Lab
jupyter lab notebooks/01_sales_pipeline_summary.ipynb

# Option B: VS Code
# Open notebooks/01_sales_pipeline_summary.ipynb in VS Code
# Select the .venv Python kernel
# Run All Cells
```

### Available Notebooks

| Notebook | Scenario | Persona |
|----------|----------|---------|
| `01_sales_pipeline_summary.ipynb` | "Show my team's pipeline and flag at-risk deals" | Sales Manager |
| `02_sales_account_briefing.ipynb` | "Prepare me for my meeting with Acme Corp" | Account Executive |
| `03_service_case_triage.ipynb` | "Triage case #12345 and suggest a response" | CSR |
| `04_service_kb_assistant.ipynb` | "How do I reset a customer's API key?" | CSR |

---

## Step 6: Verify Results

A successful notebook run will show:

1. **Environment check** — All required variables loaded ✓
2. **MCP server startup** — `salesforce-crm` server connected ✓
3. **Agent creation** — Sales/Service Agent created with MCP tools ✓
4. **Conversation** — Agent responds with real Salesforce data
5. **Citations** — Response includes Salesforce record IDs and names
6. **Cleanup** — Agent and MCP server shut down cleanly ✓

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Run `source .venv/bin/activate` and verify `pip list` shows `azure-ai-projects` |
| `AuthenticationError` from Azure | Run `az login` and verify correct subscription: `az account show` |
| `SalesforceAuthenticationFailed` | Check `SF_ACCESS_TOKEN` validity; tokens expire in ~2 hours. Re-obtain via OAuth flow or `sf org display`. |
| `INSUFFICIENT_ACCESS` from Salesforce | Verify user has API access and correct Permission Set. See [salesforce-setup.md](../../docs/salesforce-setup.md). |
| `KNOWLEDGE_DISABLED` in KB notebook | Salesforce Knowledge must be enabled by an admin with published articles. |
| MCP server timeout | Ensure `python` is in PATH and the virtual environment is activated. |
| Rate limit warnings | Reduce query frequency or check Salesforce API limit via Setup → Company Information → API Requests. |

---

## Next Steps

- **Try all 4 notebooks** to see Sales and Service scenarios
- **Modify system prompts** in `agents/sales/system_prompt.md` or `agents/service/system_prompt.md`
- **Adjust risk thresholds** in `config/risk_thresholds.yaml`
- **Add new MCP tools** — see [docs/extending-scenarios.md](../../docs/extending-scenarios.md)
- **Deploy to Azure** — see [docs/azure-setup.md](../../docs/azure-setup.md) for production deployment
- **Customize infrastructure** — edit `.bicepparam` files in `infra/bicep/env/` per environment
- **Review Bicep modules** — see `infra/bicep/modules/` for resource definitions
- **CI/CD pipeline** — push to `main` auto-deploys dev; use workflow dispatch for test/prod
