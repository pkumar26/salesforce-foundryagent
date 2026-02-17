# Incident Runbooks

Operational playbooks for common failure scenarios.

## Runbook 1 — API Rate-Limit Exceeded

**Alert**: `salesforce-api-rate-limit` fires when API usage exceeds 80% of the 24-hour limit.

### Symptoms
- MCP tools return `ErrorResponse` with message containing "REQUEST_LIMIT_EXCEEDED"
- `ApiUsageTracker` logs show usage approaching daily quota

### Immediate Actions
1. **Assess scope**: Check `ApiUsageTracker` counters in Application Insights:
   ```kql
   customMetrics
   | where name == "salesforce.api_calls"
   | summarize sum(value) by bin(timestamp, 1h)
   | order by timestamp desc
   ```
2. **Identify hot tools**: Find which MCP tools are consuming the most API calls:
   ```kql
   customEvents
   | where name startswith "mcp.tool"
   | summarize count() by tostring(customDimensions["mcp.tool.name"])
   | order by count_ desc
   ```
3. **Throttle if needed**: Set `MCP_RATE_LIMIT_MODE=restrictive` env var to disable bulk/list tools temporarily.

### Resolution
- If caused by a specific notebook: Stop the notebook kernel.
- If caused by a sync job: Pause `knowledge_sync` cron.
- Wait for the 24-hour rolling window to reset.
- Consider enabling caching for high-frequency queries (e.g., pipeline summary).

### Prevention
- Monitor `salesforce.api_calls` daily trend.
- Set per-tool `LIMIT` defaults to conservative values.
- Implement result caching for `get_pipeline_summary` and `get_case_queue_summary`.

---

## Runbook 2 — OAuth Token Refresh Failure

**Alert**: `oauth-refresh-failure` fires when token refresh returns non-200 or the refresh token is revoked.

### Symptoms
- MCP tools return `ErrorResponse` with message "INVALID_SESSION_ID" or "invalid_grant"
- `shared.auth.refresh_access_token()` raises `SalesforceAuthError`

### Immediate Actions
1. **Check token validity**:
   ```bash
   curl -H "Authorization: Bearer $SF_ACCESS_TOKEN" \
        "$SF_INSTANCE_URL/services/data/v62.0/limits"
   ```
2. **Attempt manual refresh**:
   ```bash
   curl -X POST https://login.salesforce.com/services/oauth2/token \
     -d "grant_type=refresh_token&client_id=$SF_CLIENT_ID&client_secret=$SF_CLIENT_SECRET&refresh_token=$SF_REFRESH_TOKEN"
   ```
3. **If refresh token revoked**: Re-authenticate via the OAuth flow:
   - Run the authorization URL builder: `python -c "from shared.auth import build_authorization_url; print(build_authorization_url())"`
   - Complete browser login, exchange code for new tokens.
   - Update Key Vault secrets: `az keyvault secret set --name sf-access-token --value <new_token> --vault-name <vault>`

### Resolution
- If Connected App settings changed: Verify `SF_CLIENT_ID` and `SF_CLIENT_SECRET` match the Salesforce Connected App.
- If IP restrictions: Ensure the server IP is in the Salesforce Connected App trusted IP ranges.
- If session policy: Check "Session Settings" in Salesforce Setup for timeout configuration.

### Prevention
- Set refresh token policy to "Refresh token is valid until revoked" in the Connected App.
- Monitor `oauth.refresh.failure` custom metric in Application Insights.
- Rotate secrets quarterly via Key Vault rotation policy.

---

## Runbook 3 — MCP Server Crash / Unresponsive

**Alert**: `mcp-server-health` fires when the MCP server process exits or fails to respond within 30 seconds.

### Symptoms
- Notebook cells hang indefinitely when calling MCP tools
- Azure AI Agent returns "tool connection failed" errors
- App Service health probe returns 503

### Immediate Actions
1. **Check server logs**:
   ```bash
   # If running locally (stdio transport)
   python -m mcp_servers.salesforce_crm.server 2>&1 | tail -50

   # If deployed to App Service
   az webapp log tail --name <app-name> --resource-group <rg-name>
   ```
2. **Check process status**:
   ```bash
   # Local
   ps aux | grep mcp_servers

   # App Service
   az webapp show --name <app-name> --resource-group <rg-name> --query state
   ```
3. **Restart**:
   ```bash
   # App Service
   az webapp restart --name <app-name> --resource-group <rg-name>
   ```

### Common Causes
| Cause | Fix |
|-------|-----|
| Out of memory | Increase App Service plan tier or optimize query limits |
| Import error | Check `requirements.txt` deployed matches local |
| Missing env vars | Verify all `.env.example` vars are set in App Service Configuration |
| Port conflict (SSE) | Ensure `MCP_TRANSPORT=sse` and port 8000 is available |

### Prevention
- Enable App Service "Always On" to prevent cold starts.
- Set up auto-restart with health check endpoint.
- Monitor memory usage via App Insights `performanceCounters`.

---

## Runbook 4 — OpenAI / Azure AI Model Degradation

**Alert**: `openai-latency-high` fires when P95 latency exceeds 10 seconds or error rate exceeds 5%.

### Symptoms
- Agent responses are slow (>15 seconds for simple queries)
- Agent returns empty or truncated responses
- `429 Too Many Requests` errors in logs

### Immediate Actions
1. **Check Azure OpenAI status**:
   - Visit [Azure Status](https://status.azure.com/) for service health.
   - Check Azure OpenAI resource metrics in Azure Portal.
2. **Check token usage**:
   ```kql
   dependencies
   | where target contains "openai"
   | summarize avg(duration), percentile(duration, 95) by bin(timestamp, 5m)
   ```
3. **Check rate limits**:
   ```bash
   az cognitiveservices account show \
     --name <openai-resource> --resource-group <rg-name> \
     --query "properties.quotaLimit"
   ```

### Resolution
- **429 errors**: Reduce `AZURE_AI_MODEL_CAPACITY` in Bicep params or implement exponential backoff.
- **High latency**: Reduce `max_tokens` in agent configuration, simplify system prompts.
- **Model unavailable**: Switch to fallback model by updating `AZURE_AI_MODEL_NAME` env var.

### Escalation
- If Azure-wide incident: File support ticket via Azure Portal.
- If quota-related: Request quota increase via Azure Portal > Quotas.
- Track incident in team channel with timestamps and error codes.

### Prevention
- Set up Azure Monitor alerts on OpenAI resource metrics.
- Maintain a fallback model deployment (e.g., GPT-4o-mini).
- Implement circuit breaker pattern for agent calls.
