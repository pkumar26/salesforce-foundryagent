// =============================================================================
// container-registry.bicep — Azure Container Registry for MCP server images
// Contract: specs/001-salesforce-ai-assistant/contracts/bicep-modules.md
// Only deployed when hostingMode == 'aca'
// =============================================================================

@description('Azure region')
param location string

@description('Project name for resource naming (alphanumeric only: cr{projectName})')
param projectName string

@description('ACR SKU: Basic, Standard, Premium')
@allowed(['Basic', 'Standard', 'Premium'])
param sku string = 'Basic'

@description('Whether admin user is enabled (should be false — use managed identity)')
param adminUserEnabled bool = false

@description('Resource tags')
param tags object = {}

// ACR names must be alphanumeric, 5-50 chars
var acrName = replace('cr${projectName}', '-', '')

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: acrName
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: adminUserEnabled
    publicNetworkAccess: 'Enabled'
    policies: {
      retentionPolicy: {
        status: 'disabled'
      }
    }
  }
}

// --- Outputs ---
@description('Resource ID of the Container Registry')
output acrId string = containerRegistry.id

@description('Name of the Container Registry')
output acrName string = containerRegistry.name

@description('ACR login server (e.g., crsfaidev.azurecr.io)')
output acrLoginServer string = containerRegistry.properties.loginServer
