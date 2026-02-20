# Azure Setup Guide

## Prerequisites

- Azure subscription with Owner or Contributor access
- Azure CLI v2.60+ installed (`az --version`)
- Bicep CLI v0.25+ (`az bicep version`)

## Option 1: Automated Provisioning (Recommended)

### Quick Start

```bash
# One-command deploy for development
./scripts/provision_azure.sh dev

# Preview changes before deploying
./scripts/provision_azure.sh dev --what-if

# Deploy to test/prod
./scripts/provision_azure.sh test
./scripts/provision_azure.sh prod
```

### Environment-Specific Configuration

| Parameter | Dev | Test | Prod |
|-----------|-----|------|------|
| Search SKU | free | basic | standard |
| Storage Redundancy | LRS | ZRS | GRS |
| OpenAI TPM | 10,000 | 30,000 | 80,000 |
| App Insights | Auto (ACA) | ✅ | ✅ |
| Hosting Mode | aca | aca | aca |
| Container Apps | ✅ | ✅ | ✅ |
| Container Registry | Basic | Basic | Standard |

## Option 2: Manual Provisioning

### Step 1: Resource Group

```bash
az group create \
  --name rg-salesforce-ai-dev \
  --location eastus2
```

### Step 2: Storage Account

```bash
az storage account create \
  --name stsalesforceaidev \
  --resource-group rg-salesforce-ai-dev \
  --sku Standard_LRS \
  --kind StorageV2
```

### Step 3: Key Vault

```bash
az keyvault create \
  --name kv-salesforce-ai-dev \
  --resource-group rg-salesforce-ai-dev \
  --enable-rbac-authorization
```

### Step 4: Azure OpenAI

```bash
az cognitiveservices account create \
  --name oai-salesforce-ai-dev \
  --resource-group rg-salesforce-ai-dev \
  --kind OpenAI \
  --sku S0 \
  --location eastus2

# Deploy GPT-4o model
az cognitiveservices account deployment create \
  --name oai-salesforce-ai-dev \
  --resource-group rg-salesforce-ai-dev \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-11-20" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard
```

### Step 5: Azure AI Search

```bash
az search service create \
  --name srch-salesforce-ai-dev \
  --resource-group rg-salesforce-ai-dev \
  --sku free
```

### Step 6: Azure AI Foundry (Hub + Project)

```bash
# Create the Hub
az ml workspace create \
  --kind hub \
  --name hub-salesforce-ai-dev \
  --resource-group rg-salesforce-ai-dev \
  --storage-account stsalesforceaidev \
  --key-vault kv-salesforce-ai-dev

# Create a Project under the Hub
az ml workspace create \
  --kind project \
  --name proj-salesforce-ai-dev \
  --resource-group rg-salesforce-ai-dev \
  --hub-id /subscriptions/<sub-id>/resourceGroups/rg-salesforce-ai-dev/providers/Microsoft.MachineLearningServices/workspaces/hub-salesforce-ai-dev
```

## Bicep Module Reference

### Module Architecture

```
infra/bicep/
├── main.bicep              # Orchestrator
├── main.bicepparam         # Dev defaults
├── env/
│   ├── dev.bicepparam      # free/LRS/10K
│   ├── test.bicepparam     # basic/ZRS/30K
│   └── prod.bicepparam     # standard/GRS/80K
└── modules/
    ├── storage.bicep        # Storage Account
    ├── keyvault.bicep        # Key Vault (RBAC-enabled)
    ├── app-insights.bicep    # App Insights + Log Analytics
    ├── ai-foundry.bicep      # Hub + Project
    ├── openai.bicep          # OpenAI + GPT-4o deployment
    ├── ai-search.bicep       # AI Search service
    ├── app-service.bicep     # App Service (optional, hostingMode=appService)
    ├── container-registry.bicep # ACR for Docker images (hostingMode=aca)
    └── container-apps.bicep  # ACA Environment + Container Apps (hostingMode=aca)
```

### Key Outputs

After deployment, retrieve outputs:

```bash
# Get all deployment outputs
az deployment sub show \
  --name salesforce-ai-dev \
  --query "properties.outputs" -o json
```

Key outputs used in `.env` (auto-written to `.env.azure` by `provision_azure.sh`):
- `aiFoundryProjectEndpoint` → `AZURE_AI_PROJECT_ENDPOINT`
- `openaiDeploymentName` → `AZURE_AI_MODEL_NAME`
- `keyVaultUri` → `AZURE_KEY_VAULT_URI`
- `storageAccountName` → `AZURE_STORAGE_ACCOUNT_NAME`
- `appInsightsConnectionString` → `APPLICATIONINSIGHTS_CONNECTION_STRING`
- `hostingMode` → `HOSTING_MODE`
- `mcpCrmUrl` → `MCP_CRM_URL`
- `mcpKnowledgeUrl` → `MCP_KB_URL`
- `acrLoginServer` → `ACR_LOGIN_SERVER`

### Post-Provisioning: Key Vault Secrets

Key Vault uses RBAC authorization. Before storing secrets, assign yourself the **Key Vault Secrets Officer** role:

```bash
USER_OID=$(az ad signed-in-user show --query id -o tsv)
KV_ID=$(az keyvault show --name <vault-name> --query id -o tsv)
az role assignment create \
  --role "Key Vault Secrets Officer" \
  --assignee-object-id "$USER_OID" \
  --assignee-principal-type User \
  --scope "$KV_ID"
```

Then store Salesforce credentials:

```bash
az keyvault secret set --vault-name <vault-name> --name sf-client-id --value '<consumer-key>'
az keyvault secret set --vault-name <vault-name> --name sf-client-secret --value '<consumer-secret>'
az keyvault secret set --vault-name <vault-name> --name sf-instance-url --value '<instance-url>'
az keyvault secret set --vault-name <vault-name> --name sf-access-token --value '<access-token>'
```

> **Note:** Use single quotes for values containing `!` or other shell special characters.

### Deploying Container Images (ACA)

After provisioning, deploy real MCP server images:

```bash
./scripts/deploy_app.sh dev aca
```

This builds `linux/amd64` images, pushes to ACR, configures the registry, and updates the container apps with proper port (8000) and host binding (`0.0.0.0`).

## CI/CD (GitHub Actions)

### OIDC Authentication Setup

1. Create an Azure AD App Registration:
   ```bash
   az ad app create --display-name "gh-actions-salesforce-ai"
   ```

2. Create a federated credential for GitHub:
   ```bash
   az ad app federated-credential create \
     --id <app-object-id> \
     --parameters '{
       "name": "github-main",
       "issuer": "https://token.actions.githubusercontent.com",
       "subject": "repo:<owner>/<repo>:ref:refs/heads/main",
       "audiences": ["api://AzureADTokenExchange"]
     }'
   ```

3. Set GitHub secrets:
   - `AZURE_CLIENT_ID` — App Registration client ID
   - `AZURE_TENANT_ID` — Azure AD tenant ID
   - `AZURE_SUBSCRIPTION_ID` — Target subscription
   - `AZURE_CREDENTIALS` — Service principal JSON (for `azure/login`)

### Workflows

- **ci.yml**: Runs on PR/push — lint, test, Bicep validate
- **deploy-infra.yml**: Runs on merge to main or manual dispatch — progressive deploy

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Bicep validation error | Run `az bicep build -f main.bicep` locally |
| Quota exceeded | Check regional quotas for OpenAI models |
| OIDC auth failure | Verify federated credential subject claim |
| Hub creation failure | Ensure Storage and Key Vault exist first |
