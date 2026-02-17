# Bicep Module Contracts

**Date**: 2026-02-16 | **Phase**: 1 (Design & Contracts)
**Source**: Plan IaC strategy section and Azure resource requirements from research.md

Each module below documents its **parameters** (inputs), **outputs**, and **purpose**. These contracts define what `main.bicep` passes to each module and what it receives back.

---

## Module: `storage.bicep`

**Purpose**: Provision an Azure Storage Account required as a dependency for AI Foundry Hub.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `location` | `string` | Yes | — | Azure region |
| `projectName` | `string` | Yes | — | Base name for resource naming (`st{projectName}`) |
| `redundancy` | `string` | No | `'LRS'` | Replication type: `LRS`, `ZRS`, `GRS` |
| `tags` | `object` | No | `{}` | Resource tags |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `storageAccountId` | `string` | Resource ID of the Storage Account |
| `storageAccountName` | `string` | Name of the Storage Account |

### Resource

| Resource Type | API Version |
|---------------|-------------|
| `Microsoft.Storage/storageAccounts` | `2023-05-01` |

---

## Module: `keyvault.bicep`

**Purpose**: Provision Azure Key Vault for storing Salesforce OAuth secrets (consumer key, consumer secret, refresh tokens).

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `location` | `string` | Yes | — | Azure region |
| `projectName` | `string` | Yes | — | Base name for naming (`kv-{projectName}`) |
| `sku` | `string` | No | `'standard'` | Key Vault SKU: `standard` or `premium` (HSM) |
| `enableSoftDelete` | `bool` | No | `true` | Enable soft delete |
| `softDeleteRetentionInDays` | `int` | No | `90` | Soft delete retention |
| `enableRbacAuthorization` | `bool` | No | `true` | Use RBAC instead of access policies |
| `tags` | `object` | No | `{}` | Resource tags |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `keyVaultId` | `string` | Resource ID of the Key Vault |
| `vaultUri` | `string` | Key Vault URI (e.g., `https://kv-sfai-dev.vault.azure.net/`) |
| `keyVaultName` | `string` | Name of the Key Vault |

### Resource

| Resource Type | API Version |
|---------------|-------------|
| `Microsoft.KeyVault/vaults` | `2023-07-01` |

---

## Module: `app-insights.bicep`

**Purpose**: Provision Application Insights (with backing Log Analytics workspace) for agent telemetry, MCP server observability, and Azure AI Foundry diagnostics.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `location` | `string` | Yes | — | Azure region |
| `projectName` | `string` | Yes | — | Base name for naming (`ai-{projectName}`) |
| `logAnalyticsRetentionDays` | `int` | No | `30` | Log retention in days |
| `tags` | `object` | No | `{}` | Resource tags |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `appInsightsId` | `string` | Resource ID of Application Insights |
| `connectionString` | `string` | App Insights connection string |
| `instrumentationKey` | `string` | App Insights instrumentation key |
| `logAnalyticsWorkspaceId` | `string` | Resource ID of Log Analytics workspace |

### Resources

| Resource Type | API Version |
|---------------|-------------|
| `Microsoft.OperationalInsights/workspaces` | `2023-09-01` |
| `Microsoft.Insights/components` | `2020-02-02` |

---

## Module: `ai-foundry.bicep`

**Purpose**: Provision Azure AI Foundry Hub and Project. The Hub is the top-level container; the Project is the workspace where agents are created and managed.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `location` | `string` | Yes | — | Azure region |
| `projectName` | `string` | Yes | — | Base name for naming (`hub-{projectName}`, `proj-{projectName}`) |
| `storageAccountId` | `string` | Yes | — | Resource ID of the Storage Account (from `storage.bicep`) |
| `keyVaultId` | `string` | Yes | — | Resource ID of the Key Vault (from `keyvault.bicep`) |
| `appInsightsId` | `string` | No | `''` | Resource ID of App Insights (from `app-insights.bicep`); empty if not deployed |
| `tags` | `object` | No | `{}` | Resource tags |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `hubId` | `string` | Resource ID of the AI Foundry Hub |
| `projectId` | `string` | Resource ID of the AI Foundry Project |
| `projectName` | `string` | Name of the AI Foundry Project |
| `projectEndpoint` | `string` | API endpoint for the Project (e.g., `https://proj-sfai-dev.services.ai.azure.com/api`) |

### Resources

| Resource Type | API Version | Kind |
|---------------|-------------|------|
| `Microsoft.MachineLearningServices/workspaces` | `2024-10-01` | `hub` |
| `Microsoft.MachineLearningServices/workspaces` | `2024-10-01` | `project` |

### Notes

- The Hub is a `kind: 'hub'` workspace with `storageAccount`, `keyVault`, and optional `applicationInsights` associations.
- The Project is a `kind: 'project'` workspace with `parent` set to the Hub using the `parent` property (not `/` in name).

---

## Module: `openai.bicep`

**Purpose**: Provision Azure OpenAI Service and create a GPT-4o model deployment for agent conversations.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `location` | `string` | Yes | — | Azure region |
| `projectName` | `string` | Yes | — | Base name for naming (`oai-{projectName}`) |
| `modelName` | `string` | No | `'gpt-4o'` | Model to deploy |
| `modelVersion` | `string` | No | `'2024-11-20'` | Model version |
| `capacity` | `int` | No | `10` | Deployment capacity in thousands of tokens per minute (TPM) |
| `deploymentSkuName` | `string` | No | `'GlobalStandard'` | Deployment SKU |
| `tags` | `object` | No | `{}` | Resource tags |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `openaiAccountId` | `string` | Resource ID of the OpenAI Service |
| `openaiEndpoint` | `string` | OpenAI API endpoint |
| `deploymentName` | `string` | Name of the model deployment |

### Resources

| Resource Type | API Version |
|---------------|-------------|
| `Microsoft.CognitiveServices/accounts` | `2024-10-01` |
| `Microsoft.CognitiveServices/accounts/deployments` | `2024-10-01` |

### Notes

- Deployment uses `parent` property referencing the Cognitive Services account (not `/` in name).
- Content Safety filters are enabled at the deployment level by default.

---

## Module: `ai-search.bicep`

**Purpose**: Provision Azure AI Search service for Knowledge Article RAG indexing.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `location` | `string` | Yes | — | Azure region |
| `projectName` | `string` | Yes | — | Base name for naming (`srch-{projectName}`) |
| `sku` | `string` | No | `'free'` | Search SKU: `free`, `basic`, `standard`, `standard2`, `standard3` |
| `replicaCount` | `int` | No | `1` | Number of replicas |
| `partitionCount` | `int` | No | `1` | Number of partitions |
| `tags` | `object` | No | `{}` | Resource tags |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `searchServiceId` | `string` | Resource ID of the Search Service |
| `searchServiceName` | `string` | Name of the Search Service |
| `searchEndpoint` | `string` | Search API endpoint |

### Resource

| Resource Type | API Version |
|---------------|-------------|
| `Microsoft.Search/searchServices` | `2024-06-01-preview` |

---

## Module: `app-service.bicep`

**Purpose**: Provision an App Service Plan and Web App for hosting the MCP servers in SSE mode (production deployment). **Optional** — only deployed when `deployAppService = true` in the `.bicepparam` file.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `location` | `string` | Yes | — | Azure region |
| `projectName` | `string` | Yes | — | Base name for naming (`plan-{projectName}`, `app-{projectName}`) |
| `skuName` | `string` | No | `'B1'` | App Service Plan SKU: `B1`, `S1`, `P1v3` |
| `linuxFxVersion` | `string` | No | `'PYTHON|3.11'` | Runtime stack |
| `appInsightsConnectionString` | `string` | No | `''` | App Insights connection string for auto-instrumentation |
| `keyVaultUri` | `string` | No | `''` | Key Vault URI for app settings references |
| `tags` | `object` | No | `{}` | Resource tags |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `appServicePlanId` | `string` | Resource ID of the App Service Plan |
| `appServiceId` | `string` | Resource ID of the Web App |
| `defaultHostName` | `string` | Default hostname (e.g., `app-sfai-prod.azurewebsites.net`) |

### Resources

| Resource Type | API Version |
|---------------|-------------|
| `Microsoft.Web/serverfarms` | `2023-12-01` |
| `Microsoft.Web/sites` | `2023-12-01` |

### Notes

- Web App uses system-assigned managed identity for Key Vault access.
- App settings reference Key Vault secrets using `@Microsoft.KeyVault(SecretUri=...)` syntax.
- Always HTTPS enforced. Minimum TLS 1.2.

---

## `main.bicep` Parameter Contract

These are the top-level parameters accepted by `main.bicep` and supplied by `.bicepparam` files:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `environmentName` | `string` | Yes | Environment identifier: `dev`, `test`, `prod` |
| `location` | `string` | Yes | Azure region for all resources |
| `projectName` | `string` | Yes | Base project name used for resource naming |
| `openaiModelCapacity` | `int` | Yes | GPT-4o deployment capacity (TPM in thousands) |
| `aiSearchSku` | `string` | Yes | AI Search tier: `free`, `basic`, `standard` |
| `keyVaultSku` | `string` | Yes | Key Vault tier: `standard`, `premium` |
| `storageRedundancy` | `string` | Yes | Storage replication: `LRS`, `ZRS`, `GRS` |
| `deployAppInsights` | `bool` | Yes | Whether to deploy Application Insights |
| `deployAppService` | `bool` | Yes | Whether to deploy App Service (hosted MCP) |
| `appServiceSkuName` | `string` | No | App Service Plan SKU (default: `B1`) |
| `tags` | `object` | Yes | Mandatory resource tags |

### `main.bicep` Outputs

| Output | Type | Source Module | Description |
|--------|------|---------------|-------------|
| `aiFoundryProjectEndpoint` | `string` | `ai-foundry` | Agent API endpoint |
| `openaiDeploymentName` | `string` | `openai` | Model deployment name |
| `keyVaultUri` | `string` | `keyvault` | Key Vault URI |
| `storageAccountName` | `string` | `storage` | Storage account name |
| `appInsightsConnectionString` | `string` | `app-insights` | App Insights connection string (empty if not deployed) |
| `appServiceUrl` | `string` | `app-service` | Web App URL (empty if not deployed) |
