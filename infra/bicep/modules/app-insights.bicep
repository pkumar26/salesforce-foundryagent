// =============================================================================
// Module: app-insights.bicep
// Purpose: Application Insights + Log Analytics for agent telemetry
// Contract: specs/001-salesforce-ai-assistant/contracts/bicep-modules.md
// =============================================================================

@description('Azure region')
param location string

@description('Base name for resource naming (ai-{projectName})')
param projectName string

@description('Log Analytics retention in days')
@minValue(30)
@maxValue(730)
param logAnalyticsRetentionDays int = 30

@description('Resource tags')
param tags object = {}

var logAnalyticsName = 'log-${projectName}'
var appInsightsName = 'ai-${projectName}'

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: logAnalyticsRetentionDays
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    IngestionMode: 'LogAnalytics'
  }
}

@description('Resource ID of Application Insights')
output appInsightsId string = appInsights.id

@description('App Insights connection string')
output connectionString string = appInsights.properties.ConnectionString

@description('App Insights instrumentation key')
output instrumentationKey string = appInsights.properties.InstrumentationKey

@description('Resource ID of Log Analytics workspace')
output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id

@description('Log Analytics workspace customer ID')
output logAnalyticsCustomerId string = logAnalyticsWorkspace.properties.customerId

@description('Log Analytics workspace shared key')
output logAnalyticsSharedKey string = logAnalyticsWorkspace.listKeys().primarySharedKey
