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
| App Insights | ❌ | ✅ | ✅ |
| App Service | ❌ | ❌ | ✅ (P1v3) |

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
    ├── storage.bicep       # Storage Account
    ├── keyvault.bicep       # Key Vault
    ├── app-insights.bicep   # App Insights + Log Analytics
    ├── ai-foundry.bicep     # Hub + Project
    ├── openai.bicep         # OpenAI + GPT-4o deployment
    ├── ai-search.bicep      # AI Search service
    └── app-service.bicep    # App Service (prod only)
```

### Key Outputs

After deployment, retrieve outputs:

```bash
# Get all deployment outputs
az deployment sub show \
  --name salesforce-ai-dev \
  --query "properties.outputs" -o json
```

Key outputs used in `.env`:
- `projectEndpoint` → `AZURE_AI_PROJECT_ENDPOINT`
- `openaiEndpoint` → `AZURE_OPENAI_ENDPOINT`
- `searchEndpoint` → `AZURE_AI_SEARCH_ENDPOINT`

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
