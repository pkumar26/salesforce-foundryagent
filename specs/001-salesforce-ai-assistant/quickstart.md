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
| **Docker** _(ACA only)_ | Required if deploying with Azure Container Apps hosting mode |

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

## Step 3: Choose Your Hosting Mode

The project supports two hosting modes for production deployment of MCP servers, plus a no-hosting mode for local development:

| Mode | When to use | What it deploys |
|------|-------------|-----------------|
| **`none`** (default) | Local dev / notebook demos | No hosting infra; MCP servers run via stdio in-process |
| **`appService`** | Simple PaaS deployment | App Service Plan + 2 Web Apps (zip deploy) |
| **`aca`** | Container-based, auto-scaling | ACR + ACA Environment + 2 Container Apps |

> **Default**: If you just want to run notebooks locally, leave hosting as `none`. For production, see [docs/hosting-modes.md](../../docs/hosting-modes.md) for a detailed comparison.

The hosting mode is set per environment in the `.bicepparam` file (see Step 4).

---

## Step 4: Provision Azure Resources (Bicep IaC)

All Azure resources are managed as Infrastructure as Code using **Bicep** templates in `infra/bicep/`.

### Option A: Automated provisioning script (recommended)

```bash
# Provision the dev environment (default — hostingMode=none, no hosting infra)
chmod +x scripts/provision_azure.sh
./scripts/provision_azure.sh dev

# Provision test with App Service hosting
./scripts/provision_azure.sh test

# Provision prod with ACA hosting (edit prod.bicepparam first to set hostingMode)
./scripts/provision_azure.sh prod
```

The script runs `az deployment sub create` with the matching `.bicepparam` file:

| Environment | Parameter File | Hosting Mode | Key Differences |
|-------------|---------------|--------------|------------------|
| `dev` | `infra/bicep/env/dev.bicepparam` | `none` | Free AI Search, 10K TPM, no hosting, LRS storage |
| `test` | `infra/bicep/env/test.bicepparam` | `appService` | Basic AI Search, 30K TPM, App Service B1, ZRS |
| `prod` | `infra/bicep/env/prod.bicepparam` | `appService` | Standard AI Search, 80K TPM, App Service P1v3, GRS |

To switch prod to ACA, edit `infra/bicep/env/prod.bicepparam`:
```bicep
param hostingMode = 'aca'
// param appServiceSkuName = 'P1v3'   ← remove or leave (ignored when aca)
param acrSku = 'Standard'
```

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

| Resource | Module | All envs | App Service only | ACA only |
|----------|--------|----------|-----------------|----------|
| Storage Account | `storage.bicep` | ✅ | — | — |
| Key Vault | `keyvault.bicep` | ✅ | — | — |
| AI Foundry Hub + Project | `ai-foundry.bicep` | ✅ | — | — |
| Azure OpenAI (GPT-4o) | `openai.bicep` | ✅ | — | — |
| AI Search | `ai-search.bicep` | ✅ | — | — |
| Application Insights | `app-insights.bicep` | test, prod | — | — |
| App Service Plan + Web Apps | `app-service.bicep` | — | ✅ | — |
| Container Registry | `container-registry.bicep` | — | — | ✅ |
| ACA Environment + Container Apps | `container-apps.bicep` | — | — | ✅ |

After provisioning, the script prints output values for `.env` configuration.

---

## Step 5: Deploy MCP Servers (Hosted Mode Only)

If you chose `appService` or `aca` hosting, deploy the MCP servers after provisioning:

```bash
# App Service: zip deploy
./scripts/deploy_app.sh test appService

# ACA: build Docker images, push to ACR, update container apps
./scripts/deploy_app.sh prod aca
```

For `hostingMode = none` (dev), skip this step — notebooks run MCP servers in-process via stdio.

---

## Step 6: Configure Environment

Edit `.env` with your values:

```bash
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

# MCP transport (set automatically by provision script)
MCP_TRANSPORT=stdio           # or 'sse' for hosted mode
MCP_CRM_URL=                  # set when hosting is deployed
MCP_KB_URL=                   # set when hosting is deployed

# Optional: Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=<from-azure-provisioning>
```

---

## Step 7: Run a Notebook

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

> **Note**: Notebooks work identically regardless of hosting mode. When `MCP_TRANSPORT=stdio`, the agent spawns MCP servers as subprocesses. When `MCP_TRANSPORT=sse`, the agent connects to the hosted MCP server URLs.

---

## Step 8: Verify Results

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
| Docker build fails (ACA) | Ensure Docker Desktop is running. Check `docker info` for status. |
| ACR push denied (ACA) | Run `az acr login --name <acr-name>` before pushing. |
| ACA container crash loop | Check container logs: `az containerapp logs show --name <app> --resource-group <rg>` |

---

## Next Steps

- **Try all 4 notebooks** to see Sales and Service scenarios
- **Compare hosting modes** — see [docs/hosting-modes.md](../../docs/hosting-modes.md)
- **Switch hosting mode** — edit your environment's `.bicepparam` file and re-provision
- **Modify system prompts** in `agents/sales/system_prompt.md` or `agents/service/system_prompt.md`
- **Adjust risk thresholds** in `config/risk_thresholds.yaml`
- **Add new MCP tools** — see [docs/extending-scenarios.md](../../docs/extending-scenarios.md)
- **Deploy to Azure** — see [docs/azure-setup.md](../../docs/azure-setup.md) for production deployment
- **Customize infrastructure** — edit `.bicepparam` files in `infra/bicep/env/` per environment
- **Review Bicep modules** — see `infra/bicep/modules/` for resource definitions
- **CI/CD pipeline** — push to `main` auto-deploys dev; use workflow dispatch for test/prod
