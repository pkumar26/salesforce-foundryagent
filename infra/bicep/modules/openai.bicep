// =============================================================================
// openai.bicep — Azure OpenAI Service + GPT-4o Deployment
// Purpose: Provision Azure OpenAI Service and create a GPT-4o model deployment
// Contract: specs/001-salesforce-ai-assistant/contracts/bicep-modules.md
// =============================================================================

@description('Azure region')
param location string

@description('Base name for resource naming')
param projectName string

@description('Model to deploy')
param modelName string = 'gpt-4o'

@description('Model version')
param modelVersion string = '2024-11-20'

@description('Deployment capacity in thousands of tokens per minute (TPM)')
param capacity int = 10

@description('Deployment SKU')
param deploymentSkuName string = 'GlobalStandard'

@description('Resource tags')
param tags object = {}

// --- Azure OpenAI Service ---
resource openaiAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: 'oai-${projectName}'
  location: location
  kind: 'OpenAI'
  tags: tags
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    customSubDomainName: 'oai-${projectName}'
  }
}

// --- GPT-4o Model Deployment ---
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openaiAccount
  name: '${modelName}-deployment'
  sku: {
    name: deploymentSkuName
    capacity: capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
  }
}

// --- Outputs ---
@description('Resource ID of the OpenAI Service')
output openaiAccountId string = openaiAccount.id

@description('OpenAI API endpoint')
output openaiEndpoint string = openaiAccount.properties.endpoint

@description('Name of the model deployment')
output deploymentName string = deployment.name
