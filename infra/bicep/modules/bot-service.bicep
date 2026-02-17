// Azure Bot Service registration for Microsoft Teams integration
// Reference: T054a — Bot registration for Teams channel

@description('Bot display name')
param botName string

@description('Microsoft App ID for the bot (AAD app registration)')
param msaAppId string

@description('MCP server endpoint URL')
param messagingEndpoint string = ''

@description('Environment name')
param environment string

@description('Location for the Bot Service')
param location string = 'global'

@description('Bot SKU')
@allowed(['F0', 'S1'])
param sku string = 'F0'

@description('Tags for the resource')
param tags object = {}

resource botService 'Microsoft.BotService/botServices@2022-09-15' = {
  name: '${botName}-${environment}'
  location: location
  sku: {
    name: sku
  }
  kind: 'azurebot'
  tags: tags
  properties: {
    displayName: botName
    msaAppId: msaAppId
    endpoint: messagingEndpoint
    msaAppType: 'SingleTenant'
    disableLocalAuth: false
    schemaTransformationVersion: '1.3'
  }
}

// Enable Microsoft Teams channel
resource teamsChannel 'Microsoft.BotService/botServices/channels@2022-09-15' = {
  parent: botService
  name: 'MsTeamsChannel'
  location: location
  properties: {
    channelName: 'MsTeamsChannel'
    properties: {
      isEnabled: true
      enableCalling: false
    }
  }
}

@description('Bot Service resource ID')
output botServiceId string = botService.id

@description('Bot Service name')
output botServiceName string = botService.name
