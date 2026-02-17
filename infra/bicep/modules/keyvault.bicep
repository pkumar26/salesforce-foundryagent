// =============================================================================
// Module: keyvault.bicep
// Purpose: Provision Azure Key Vault for Salesforce OAuth secrets
// Contract: specs/001-salesforce-ai-assistant/contracts/bicep-modules.md
// =============================================================================

@description('Azure region for the Key Vault')
param location string

@description('Base name for resource naming (kv-{projectName})')
param projectName string

@description('Key Vault SKU: standard or premium (HSM)')
@allowed(['standard', 'premium'])
param sku string = 'standard'

@description('Enable soft delete')
param enableSoftDelete bool = true

@description('Soft delete retention in days')
@minValue(7)
@maxValue(90)
param softDeleteRetentionInDays int = 90

@description('Use RBAC instead of access policies')
param enableRbacAuthorization bool = true

@description('Resource tags')
param tags object = {}

var keyVaultName = 'kv-${projectName}'

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: length(keyVaultName) > 24 ? substring(keyVaultName, 0, 24) : keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: sku
    }
    tenantId: tenant().tenantId
    enableSoftDelete: enableSoftDelete
    softDeleteRetentionInDays: softDeleteRetentionInDays
    enableRbacAuthorization: enableRbacAuthorization
    enablePurgeProtection: true
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

@description('Resource ID of the Key Vault')
output keyVaultId string = keyVault.id

@description('Key Vault URI')
output vaultUri string = keyVault.properties.vaultUri

@description('Name of the Key Vault')
output keyVaultName string = keyVault.name
