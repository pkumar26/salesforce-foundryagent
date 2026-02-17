// =============================================================================
// ai-foundry.bicep — Azure AI Foundry Hub + Project
// Purpose: Provision AI Foundry Hub and Project workspace for agent management
// Contract: specs/001-salesforce-ai-assistant/contracts/bicep-modules.md
// =============================================================================

@description('Azure region')
param location string

@description('Base name for resource naming')
param projectName string

@description('Resource ID of the Storage Account (from storage.bicep)')
param storageAccountId string

@description('Resource ID of the Key Vault (from keyvault.bicep)')
param keyVaultId string

@description('Resource ID of App Insights (from app-insights.bicep); empty if not deployed')
param appInsightsId string = ''

@description('Resource tags')
param tags object = {}

// --- AI Foundry Hub ---
resource hub 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: 'hub-${projectName}'
  location: location
  kind: 'hub'
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'AI Foundry Hub - ${projectName}'
    description: 'Azure AI Foundry Hub for Salesforce AI Assistant'
    storageAccount: storageAccountId
    keyVault: keyVaultId
    applicationInsights: !empty(appInsightsId) ? appInsightsId : null
    publicNetworkAccess: 'Enabled'
  }
}

// --- AI Foundry Project ---
resource project 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: 'proj-${projectName}'
  location: location
  kind: 'project'
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'Salesforce AI Assistant Project - ${projectName}'
    description: 'AI Foundry Project for Salesforce AI Assistant agents'
    hubResourceId: hub.id
    publicNetworkAccess: 'Enabled'
  }
}

// --- Outputs ---
@description('Resource ID of the AI Foundry Hub')
output hubId string = hub.id

@description('Resource ID of the AI Foundry Project')
output projectId string = project.id

@description('Name of the AI Foundry Project')
output projectName string = project.name

@description('API endpoint for the Project')
output projectEndpoint string = 'https://${project.name}.services.ai.azure.com/api'
