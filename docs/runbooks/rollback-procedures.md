# Rollback Procedures

## Infrastructure Rollback (Azure)

### Bicep Deployment Rollback

Azure Resource Manager keeps deployment history. To revert to a previous state:

```bash
# List recent deployments
az deployment sub list --query "[].{name:name, time:properties.timestamp, state:properties.provisioningState}" -o table

# Show a specific past deployment
az deployment sub show --name <previous-deployment-name> --query properties.outputs

# Re-deploy the previous template version
git log --oneline infra/bicep/main.bicep  # find the last known-good commit
git checkout <commit-sha> -- infra/bicep/
./scripts/provision_azure.sh <environment>
```

### Resource-Level Rollback

| Resource | Rollback Method |
|----------|----------------|
| AI Foundry / OpenAI | Re-deploy Bicep module — models are stateless |
| AI Search | Re-create index from Knowledge sync pipeline |
| Key Vault | Soft-delete enabled, recover secrets within 90 days |
| Storage | Blob versioning enabled, restore previous versions |
| App Service | Deployment slots for zero-downtime swap-back |

### App Service Slot Swap

```bash
# Deploy new version to staging slot
az webapp deployment source config-zip --resource-group rg-sf-ai-assistant \
  --name app-sf-ai-assistant-crm --slot staging --src package.zip

# Test staging slot
curl https://app-sf-ai-assistant-crm-staging.azurewebsites.net/health

# Swap staging → production
az webapp deployment slot swap --resource-group rg-sf-ai-assistant \
  --name app-sf-ai-assistant-crm --slot staging --target-slot production

# If issues detected — swap back
az webapp deployment slot swap --resource-group rg-sf-ai-assistant \
  --name app-sf-ai-assistant-crm --slot production --target-slot staging
```

## Code Rollback

### MCP Server Changes

```bash
# Identify the problematic commit
git log --oneline --since="2 days ago" -- mcp_servers/

# Revert a specific commit
git revert <commit-sha>
git push origin main

# CI/CD will automatically re-deploy
```

### Configuration Rollback

Environment variables and secrets:

```bash
# Key Vault — restore a previous secret version
az keyvault secret list-versions --vault-name <vault> --name sf-client-secret \
  --query "[].{version:id, created:attributes.created, enabled:attributes.enabled}" -o table

# Restore a specific version
az keyvault secret set-attributes --vault-name <vault> --name sf-client-secret \
  --version <old-version-id> --enabled true
```

## Knowledge Index Rollback

```bash
# Re-sync from Salesforce (rebuilds the index)
python -c "
import asyncio
from shared.knowledge_sync import sync_knowledge_articles
asyncio.run(sync_knowledge_articles(full_sync=True))
"
```

## Decision Matrix

| Severity | Action | Timeframe |
|----------|--------|-----------|
| **P1 — Service Down** | Slot swap or revert last deploy | < 15 min |
| **P2 — Degraded** | Revert config change or scale up | < 30 min |
| **P3 — Feature bug** | Git revert + CI/CD redeploy | < 2 hours |
| **P4 — Cosmetic** | Fix forward in next sprint | Next release |
