// Monitor alert rules for Salesforce AI Assistant
// Reference: T053b — API rate-limit, MCP error rate, OAuth failures

@description('Application Insights resource ID')
param appInsightsId string

@description('Action group resource ID for alert notifications')
param actionGroupId string

@description('Environment name')
param environment string

// Alert 1: Salesforce API Rate-Limit > 80%
resource apiRateLimitAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: 'sf-api-rate-limit-${environment}'
  location: 'global'
  properties: {
    description: 'Salesforce API usage has exceeded 80% of daily limit'
    severity: 2
    enabled: true
    scopes: [
      appInsightsId
    ]
    evaluationFrequency: 'PT15M'
    windowSize: 'PT1H'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'SalesforceApiRateLimit'
          metricNamespace: 'Azure.ApplicationInsights'
          metricName: 'customMetrics/salesforce.api_usage_pct'
          operator: 'GreaterThan'
          threshold: 80
          timeAggregation: 'Maximum'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    actions: [
      {
        actionGroupId: actionGroupId
      }
    ]
  }
}

// Alert 2: MCP Server Error Rate > 2%
resource mcpErrorRateAlert 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = {
  name: 'mcp-error-rate-${environment}'
  location: resourceGroup().location
  properties: {
    description: 'MCP server tool error rate exceeds 2%'
    severity: 2
    enabled: true
    scopes: [
      appInsightsId
    ]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      allOf: [
        {
          query: '''
            let total = customEvents
              | where name startswith "mcp.tool"
              | summarize total=count() by bin(TimeGenerated, 15m);
            let errors = customEvents
              | where name startswith "mcp.tool"
              | where customDimensions["mcp.tool.success"] == "False"
              | summarize errors=count() by bin(TimeGenerated, 15m);
            total
              | join kind=leftouter errors on TimeGenerated
              | extend error_pct = iff(total > 0, todouble(errors) / todouble(total) * 100, 0.0)
              | where error_pct > 2
          '''
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 3
            minFailingPeriodsToAlert: 2
          }
        }
      ]
    }
    actions: {
      actionGroups: [
        actionGroupId
      ]
    }
  }
}

// Alert 3: OAuth Refresh Failures
resource oauthFailureAlert 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = {
  name: 'oauth-refresh-failure-${environment}'
  location: resourceGroup().location
  properties: {
    description: 'OAuth token refresh failures detected'
    severity: 1
    enabled: true
    scopes: [
      appInsightsId
    ]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      allOf: [
        {
          query: '''
            traces
            | where message contains "SalesforceAuthError"
              or message contains "invalid_grant"
              or message contains "INVALID_SESSION_ID"
            | summarize count() by bin(TimeGenerated, 15m)
            | where count_ > 0
          '''
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: {
      actionGroups: [
        actionGroupId
      ]
    }
  }
}
