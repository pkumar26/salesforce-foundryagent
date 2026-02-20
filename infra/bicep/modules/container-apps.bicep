// =============================================================================
// container-apps.bicep — ACA Environment + Container Apps for MCP servers
// Contract: specs/001-salesforce-ai-assistant/contracts/bicep-modules.md
// Only deployed when hostingMode == 'aca'
// =============================================================================

@description('Azure region')
param location string

@description('Project name for resource naming')
param projectName string

@description('Log Analytics workspace customer ID (from app-insights.bicep)')
param logAnalyticsCustomerId string

@secure()
@description('Log Analytics workspace shared key (from app-insights.bicep)')
param logAnalyticsSharedKey string

@description('ACR login server for image pull (from container-registry.bicep)')
param acrLoginServer string

@description('Container image tag')
param containerImageTag string = 'latest'

@description('Application Insights connection string')
param appInsightsConnectionString string = ''

@description('Key Vault URI for secret references')
param keyVaultUri string = ''

@description('Workload profile: Consumption or D4')
@allowed(['Consumption', 'D4'])
param workloadProfile string = 'Consumption'

@description('Minimum replica count (0 enables scale-to-zero)')
@minValue(0)
param minReplicas int = 0

@description('Maximum replica count')
@minValue(1)
@maxValue(10)
param maxReplicas int = 3

@description('Resource tags')
param tags object = {}

// --- ACA Environment ---
resource acaEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-${projectName}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsSharedKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

// --- CRM MCP Server Container App ---
resource crmApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-${projectName}-crm'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: acaEnvironment.id
    workloadProfileName: 'Consumption'
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
      registries: [
        {
          server: acrLoginServer
          identity: 'system'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'sfai-crm'
          image: '${acrLoginServer}/sfai-crm:${containerImageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
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
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              periodSeconds: 30
              failureThreshold: 3
              initialDelaySeconds: 10
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              periodSeconds: 10
              failureThreshold: 3
              initialDelaySeconds: 5
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// --- Knowledge MCP Server Container App ---
resource knowledgeApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-${projectName}-knowledge'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: acaEnvironment.id
    workloadProfileName: 'Consumption'
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
      registries: [
        {
          server: acrLoginServer
          identity: 'system'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'sfai-knowledge'
          image: '${acrLoginServer}/sfai-knowledge:${containerImageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
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
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              periodSeconds: 30
              failureThreshold: 3
              initialDelaySeconds: 10
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              periodSeconds: 10
              failureThreshold: 3
              initialDelaySeconds: 5
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// --- AcrPull role assignment for CRM app ---
// Role definition ID for AcrPull: 7f951dda-4ed3-4680-a7ca-43fe172d538d
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource crmAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(crmApp.id, acrPullRoleId, acrLoginServer)
  properties: {
    principalId: crmApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
  }
}

// --- AcrPull role assignment for Knowledge app ---
resource knowledgeAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(knowledgeApp.id, acrPullRoleId, acrLoginServer)
  properties: {
    principalId: knowledgeApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
  }
}

// --- Outputs ---
@description('Resource ID of the ACA Environment')
output environmentId string = acaEnvironment.id

@description('FQDN of the CRM MCP server')
output crmAppFqdn string = crmApp.properties.configuration.ingress.fqdn

@description('FQDN of the Knowledge MCP server')
output knowledgeAppFqdn string = knowledgeApp.properties.configuration.ingress.fqdn

@description('Name of the CRM Container App')
output crmAppName string = crmApp.name

@description('Name of the Knowledge Container App')
output knowledgeAppName string = knowledgeApp.name

@description('CRM app system-assigned managed identity principal ID')
output crmPrincipalId string = crmApp.identity.principalId

@description('Knowledge app system-assigned managed identity principal ID')
output knowledgePrincipalId string = knowledgeApp.identity.principalId
