// =============================================================================
// app-service.bicep — Azure App Service for hosted MCP servers (SSE transport)
// Contract: specs/001-salesforce-ai-assistant/contracts/bicep-modules.md
// =============================================================================

@description('Azure region')
param location string

@description('Project name for resource naming')
param projectName string

@description('App Service Plan SKU name')
@allowed(['B1', 'B2', 'B3', 'S1', 'S2', 'S3', 'P1v3', 'P2v3', 'P3v3'])
param skuName string = 'B1'

@description('Application Insights connection string (empty to skip)')
param appInsightsConnectionString string = ''

@description('Key Vault URI for secret references')
param keyVaultUri string = ''

@description('Tags')
param tags object = {}

// --- App Service Plan ---
resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: 'asp-${projectName}'
  location: location
  tags: tags
  sku: {
    name: skuName
  }
  kind: 'linux'
  properties: {
    reserved: true // Linux
  }
}

// --- Web App (CRM MCP Server) ---
resource webAppCrm 'Microsoft.Web/sites@2023-12-01' = {
  name: 'app-${projectName}-crm'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      alwaysOn: skuName != 'B1' // AlwaysOn not available on Basic B1
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      appSettings: [
        {
          name: 'MCP_TRANSPORT'
          value: 'sse'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
        {
          name: 'KEY_VAULT_URI'
          value: keyVaultUri
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '0'
        }
      ]
    }
  }
}

// --- Web App (Knowledge MCP Server) ---
resource webAppKnowledge 'Microsoft.Web/sites@2023-12-01' = {
  name: 'app-${projectName}-knowledge'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      alwaysOn: skuName != 'B1'
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      appSettings: [
        {
          name: 'MCP_TRANSPORT'
          value: 'sse'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
        {
          name: 'KEY_VAULT_URI'
          value: keyVaultUri
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '0'
        }
      ]
    }
  }
}

// --- Outputs ---
@description('CRM MCP server default hostname')
output defaultHostName string = webAppCrm.properties.defaultHostName

@description('CRM MCP server app name')
output crmAppName string = webAppCrm.name

@description('Knowledge MCP server app name')
output knowledgeAppName string = webAppKnowledge.name

@description('CRM managed identity principal ID')
output crmPrincipalId string = webAppCrm.identity.principalId

@description('Knowledge managed identity principal ID')
output knowledgePrincipalId string = webAppKnowledge.identity.principalId
