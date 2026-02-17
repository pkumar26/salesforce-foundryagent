// =============================================================================
// main.bicep — Orchestrator
// Purpose: Compose all infrastructure modules for the Salesforce AI Assistant
// Contract: specs/001-salesforce-ai-assistant/contracts/bicep-modules.md
// =============================================================================

targetScope = 'subscription'

// --- Parameters (typed) ---
@description('Environment identifier: dev, test, prod')
@allowed(['dev', 'test', 'prod'])
param environmentName string

@description('Azure region for all resources')
param location string

@description('Base project name used for resource naming')
param projectName string

@description('GPT-4o deployment capacity (TPM in thousands)')
param openaiModelCapacity int

@description('AI Search tier')
@allowed(['free', 'basic', 'standard', 'standard2', 'standard3'])
param aiSearchSku string

@description('Key Vault tier')
@allowed(['standard', 'premium'])
param keyVaultSku string

@description('Storage replication type')
@allowed(['LRS', 'ZRS', 'GRS'])
param storageRedundancy string

@description('Whether to deploy Application Insights')
param deployAppInsights bool

@description('Hosting mode for MCP servers: none (notebooks only), appService, or aca')
@allowed(['none', 'appService', 'aca'])
param hostingMode string = 'aca'

@description('App Service Plan SKU (used only when hostingMode == appService)')
param appServiceSkuName string = 'B1'

@description('ACR SKU (used only when hostingMode == aca)')
@allowed(['Basic', 'Standard', 'Premium'])
param acrSku string = 'Basic'

@description('Container image tag (used only when hostingMode == aca)')
param containerImageTag string = 'latest'

@description('Mandatory resource tags')
param tags object

// --- Resource Group ---
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-${projectName}'
  location: location
  tags: tags
}

// --- Foundation modules (no dependencies) ---
module storage 'modules/storage.bicep' = {
  scope: rg
  name: 'storage-deployment'
  params: {
    location: location
    projectName: projectName
    redundancy: storageRedundancy
    tags: tags
  }
}

module keyvault 'modules/keyvault.bicep' = {
  scope: rg
  name: 'keyvault-deployment'
  params: {
    location: location
    projectName: projectName
    sku: keyVaultSku
    tags: tags
  }
}

module appInsights 'modules/app-insights.bicep' = if (deployAppInsights) {
  scope: rg
  name: 'app-insights-deployment'
  params: {
    location: location
    projectName: projectName
    tags: tags
  }
}

// --- AI modules (depend on foundation) ---
module aiFoundry 'modules/ai-foundry.bicep' = {
  scope: rg
  name: 'ai-foundry-deployment'
  params: {
    location: location
    projectName: projectName
    storageAccountId: storage.outputs.storageAccountId
    keyVaultId: keyvault.outputs.keyVaultId
    appInsightsId: deployAppInsights ? appInsights.outputs.appInsightsId : ''
    tags: tags
  }
}

module openai 'modules/openai.bicep' = {
  scope: rg
  name: 'openai-deployment'
  params: {
    location: location
    projectName: projectName
    capacity: openaiModelCapacity
    tags: tags
  }
}

module aiSearch 'modules/ai-search.bicep' = {
  scope: rg
  name: 'ai-search-deployment'
  params: {
    location: location
    projectName: projectName
    sku: aiSearchSku
    tags: tags
  }
}

// --- Optional: App Service for hosted MCP (SSE) ---
module appService 'modules/app-service.bicep' = if (hostingMode == 'appService') {
  scope: rg
  name: 'app-service-deployment'
  params: {
    location: location
    projectName: projectName
    skuName: appServiceSkuName
    appInsightsConnectionString: deployAppInsights ? appInsights.outputs.connectionString : ''
    keyVaultUri: keyvault.outputs.vaultUri
    tags: tags
  }
}

// --- Optional: Container Registry for ACA ---
module containerRegistry 'modules/container-registry.bicep' = if (hostingMode == 'aca') {
  scope: rg
  name: 'container-registry-deployment'
  params: {
    location: location
    projectName: projectName
    sku: acrSku
    tags: tags
  }
}

// --- Optional: Azure Container Apps for hosted MCP (SSE) ---
module containerApps 'modules/container-apps.bicep' = if (hostingMode == 'aca') {
  scope: rg
  name: 'container-apps-deployment'
  params: {
    location: location
    projectName: projectName
    logAnalyticsWorkspaceId: deployAppInsights ? appInsights.outputs.logAnalyticsWorkspaceId : ''
    acrLoginServer: hostingMode == 'aca' ? containerRegistry.outputs.acrLoginServer : ''
    containerImageTag: containerImageTag
    appInsightsConnectionString: deployAppInsights ? appInsights.outputs.connectionString : ''
    keyVaultUri: keyvault.outputs.vaultUri
    tags: tags
  }
}

// --- Outputs (consumed by provision_azure.sh → .env) ---
@description('Agent API endpoint')
output aiFoundryProjectEndpoint string = aiFoundry.outputs.projectEndpoint

@description('Model deployment name')
output openaiDeploymentName string = openai.outputs.deploymentName

@description('Key Vault URI')
output keyVaultUri string = keyvault.outputs.vaultUri

@description('Storage account name')
output storageAccountName string = storage.outputs.storageAccountName

@description('App Insights connection string (empty if not deployed)')
output appInsightsConnectionString string = deployAppInsights ? appInsights.outputs.connectionString : ''

@description('The hosting mode used for this deployment')
output hostingMode string = hostingMode

@description('CRM MCP server URL (empty if hostingMode == none)')
output mcpCrmUrl string = hostingMode == 'appService' ? 'https://${appService.outputs.defaultHostName}' : hostingMode == 'aca' ? 'https://${containerApps.outputs.crmAppFqdn}' : ''

@description('Knowledge MCP server URL (empty if hostingMode == none)')
output mcpKnowledgeUrl string = hostingMode == 'appService' ? 'https://app-${projectName}-knowledge.azurewebsites.net' : hostingMode == 'aca' ? 'https://${containerApps.outputs.knowledgeAppFqdn}' : ''

@description('ACR login server (empty if hostingMode != aca)')
output acrLoginServer string = hostingMode == 'aca' ? containerRegistry.outputs.acrLoginServer : ''
