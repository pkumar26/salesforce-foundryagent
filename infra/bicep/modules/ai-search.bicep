// =============================================================================
// ai-search.bicep — Azure AI Search Service
// Purpose: Provision Azure AI Search service for Knowledge Article RAG indexing
// Contract: specs/001-salesforce-ai-assistant/contracts/bicep-modules.md
// =============================================================================

@description('Azure region')
param location string

@description('Base name for resource naming')
param projectName string

@description('Search SKU: free, basic, standard, standard2, standard3')
@allowed(['free', 'basic', 'standard', 'standard2', 'standard3'])
param sku string = 'free'

@description('Number of replicas')
param replicaCount int = 1

@description('Number of partitions')
param partitionCount int = 1

@description('Resource tags')
param tags object = {}

// --- Azure AI Search Service ---
resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: 'srch-${projectName}'
  location: location
  tags: tags
  sku: {
    name: sku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: sku == 'free' ? 1 : replicaCount
    partitionCount: sku == 'free' ? 1 : partitionCount
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
  }
}

// --- Outputs ---
@description('Resource ID of the Search Service')
output searchServiceId string = searchService.id

@description('Name of the Search Service')
output searchServiceName string = searchService.name

@description('Search API endpoint')
output searchEndpoint string = 'https://${searchService.name}.search.windows.net'
