# Hosting Modes: App Service vs Azure Container Apps

**Date**: 2026-02-16 | **Source**: [research.md](../specs/001-salesforce-ai-assistant/research.md) Sections 11–20

## Overview

The Salesforce AI Assistant supports two hosting modes for MCP servers in production, plus a notebook-only mode for development:

| Mode | Value | Description |
|------|-------|-------------|
| **None** | `none` | No hosting deployed. MCP servers run locally via `stdio` transport. Ideal for development and notebook demos. |
| **App Service** | `appService` | Azure App Service (PaaS). Zip deploy from source. Simpler operational model. |
| **Azure Container Apps** | `aca` | Managed container platform. Docker images pushed to ACR. Scale-to-zero, pay-per-use. |

The hosting mode is controlled by a single `hostingMode` parameter in the `.bicepparam` file for each environment.

## Comparison Table

| Aspect | App Service | Azure Container Apps |
|--------|------------|---------------------|
| **Compute model** | PaaS Web App (Linux) | Managed container platform |
| **Runtime** | `PYTHON\|3.11` (built-in stack) | Custom Docker image |
| **Deployment artifact** | Zip deploy (`SCM_DO_BUILD_DURING_DEPLOYMENT`) | Container image push to ACR |
| **Scaling** | App Service Plan SKU (manual or autoscale rules) | KEDA-based autoscale (HTTP concurrency) |
| **Scale-to-zero** | ❌ No | ✅ Yes (Consumption plan) |
| **Ingress** | `*.azurewebsites.net` | `*.region.azurecontainerapps.io` |
| **Managed identity** | System-assigned | System-assigned |
| **Environment config** | App Settings (portal / Bicep) | Container App env vars + secrets |
| **Container registry** | Not needed | Azure Container Registry (ACR) required |
| **Health probes** | Built-in platform probes | Custom liveness + readiness at `/health` |

## Cost Analysis

| Scenario | App Service (B1) | App Service (S1) | ACA (Consumption) | ACA (Dedicated D4) |
|----------|------------------|-------------------|--------------------|---------------------|
| Monthly cost (idle) | ~$13/mo | ~$55/mo | ~$0/mo | ~$150/mo |
| Monthly cost (light, <50 users) | ~$13/mo | ~$55/mo | ~$5–15/mo | ~$150/mo |
| Scale-to-zero | ❌ | ❌ | ✅ | ❌ |
| Auto-scale | Plan change | Rule-based | KEDA (automatic) | KEDA (automatic) |
| SLA | 99.95% | 99.95% | 99.95% | 99.95% |
| Docker/ACR required | ❌ | ❌ | ✅ | ✅ |

## Security Parity

Both hosting modes achieve an identical security posture:

| Control | App Service | Azure Container Apps |
|---------|------------|---------------------|
| Managed Identity → Key Vault | System-assigned MI + RBAC | System-assigned MI + RBAC |
| TLS 1.2+ | Built-in | Built-in |
| HTTPS-only | `httpsOnly: true` | Ingress config |
| Secret management | App Settings + KV refs | Secrets + KV refs |
| Network isolation | VNet integration (optional) | ACA Environment VNet (optional) |
| Image provenance | N/A (source deploy) | ACR (private, no admin key) |
| Vulnerability scanning | N/A | ACR + Defender for Containers |
| FTPS disabled | `ftpsState: 'Disabled'` | N/A (no FTP concept) |

**Additional ACA security**:
- ACR admin credentials disabled; pull via managed identity only
- Container App revisions are immutable — rollback is a revision switch
- ACA ingress can restrict traffic to internal VNet

## Recommendation Guidance

| Scenario | Recommended Mode | Rationale |
|----------|-----------------|-----------|
| Development / demos | `none` | Use notebooks with stdio transport. Zero infra cost. |
| Demo / intermittent workloads | `aca` (Consumption) | Scale-to-zero eliminates idle cost. Pay only when queries are served. |
| Operational simplicity | `appService` | No container pipeline required. Zip deploy from source. Fewer moving parts. |
| Production (steady traffic) | `appService` (S1/P1v3) | Predictable cost, AlwaysOn, proven operational model. |
| Production (variable traffic) | `aca` (Consumption or D4) | Auto-scaling with KEDA. Handles traffic spikes efficiently. |

## Migration from `deployAppService` to `hostingMode`

The original boolean parameter `deployAppService` has been replaced by the `hostingMode` enum:

| Old Parameter | Old Value | New Parameter | New Value |
|---------------|-----------|---------------|-----------|
| `deployAppService` | `false` | `hostingMode` | `'none'` |
| `deployAppService` | `true` | `hostingMode` | `'appService'` |
| _(new)_ | _(new)_ | `hostingMode` | `'aca'` |

### Steps to Migrate

1. **Update `.bicepparam` files**: Replace `param deployAppService = false/true` with `param hostingMode = 'none'/'appService'/'aca'`
2. **Remove `deployAppService`** from `main.bicep` parameters
3. **Add ACA-specific parameters** (only needed when `hostingMode = 'aca'`):
   - `acrSku`: ACR SKU (`'Basic'`, `'Standard'`, `'Premium'`)
   - `containerImageTag`: Container image tag (default: `'latest'`)
4. **Update CI/CD**: Add `HOSTING_MODE` input to deployment workflows
5. **Update `provision_azure.sh`**: Extract new outputs (`hostingMode`, `mcpCrmUrl`, `mcpKnowledgeUrl`, `acrLoginServer`)

## Configuration

### Environment Variables (hosting-agnostic)

The following environment variables abstract the hosting difference. Application code uses these regardless of hosting mode:

| Variable | App Service | ACA | Notebook (stdio) |
|----------|------------|-----|-------------------|
| `MCP_TRANSPORT` | `sse` | `sse` | `stdio` |
| `MCP_CRM_URL` | `https://app-sfai-prod-crm.azurewebsites.net` | `https://ca-sfai-prod-crm.<region>.azurecontainerapps.io` | _(not set)_ |
| `MCP_KB_URL` | `https://app-sfai-prod-knowledge.azurewebsites.net` | `https://ca-sfai-prod-knowledge.<region>.azurecontainerapps.io` | _(not set)_ |

### Bicep Parameters per Environment

| Parameter | Dev | Test | Prod |
|-----------|-----|------|------|
| `hostingMode` | `'none'` | `'appService'` or `'aca'` | `'appService'` or `'aca'` |
| `appServiceSkuName` | — | `'B1'` | `'P1v3'` |
| `acrSku` | — | `'Basic'` | `'Standard'` |
| `containerImageTag` | — | `'latest'` | git SHA |

## Deployment

### App Service Deployment

```bash
./scripts/deploy_app.sh test appService
```

This creates a zip package and deploys via `az webapp deploy`.

### ACA Deployment

```bash
./scripts/deploy_app.sh prod aca
```

This builds Docker images (using the multi-stage `Dockerfile`), pushes to ACR, and updates the Container Apps.

### Automated (CI/CD)

The `deploy-infra.yml` workflow deploys infrastructure (including the hosting resources). Application deployment is handled by `deploy_app.sh` called from the pipeline with the appropriate hosting mode.
