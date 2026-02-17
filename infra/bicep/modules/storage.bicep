// =============================================================================
// Module: storage.bicep
// Purpose: Provision Azure Storage Account (AI Foundry dependency)
// Contract: specs/001-salesforce-ai-assistant/contracts/bicep-modules.md
// =============================================================================

@description('Azure region for the Storage Account')
param location string

@description('Base name for resource naming (st{projectName})')
param projectName string

@description('Storage replication type')
@allowed(['LRS', 'ZRS', 'GRS'])
param redundancy string = 'LRS'

@description('Resource tags')
param tags object = {}

// Storage account names must be 3-24 chars, lowercase alphanumeric only
var storageAccountName = toLower(replace('st${projectName}', '-', ''))

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: length(storageAccountName) > 24 ? substring(storageAccountName, 0, 24) : storageAccountName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_${redundancy}'
  }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

@description('Resource ID of the Storage Account')
output storageAccountId string = storageAccount.id

@description('Name of the Storage Account')
output storageAccountName string = storageAccount.name
