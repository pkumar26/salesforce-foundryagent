#!/usr/bin/env bash
# =============================================================================
# deploy_app.sh — Unified deployment for MCP servers
# Supports App Service (zip deploy) and Azure Container Apps (Docker + ACR)
#
# Usage:
#   ./scripts/deploy_app.sh <environment> [hosting-mode]
#
# hosting-mode: auto-detected from .env.azure HOSTING_MODE, or pass explicitly:
#   appService  — Zip deploy to Azure App Service
#   aca         — Docker build → ACR push → ACA update
#   none        — No-op (notebook-only mode)
#
# Examples:
#   ./scripts/deploy_app.sh dev              # No-op (hostingMode=none in dev)
#   ./scripts/deploy_app.sh test appService  # Zip deploy to App Service
#   ./scripts/deploy_app.sh prod aca         # Docker build + push + ACA update
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Arguments ---
ENVIRONMENT="${1:?Usage: deploy_app.sh <environment> [hosting-mode]}"
HOSTING_MODE="${2:-}"

# --- Validate environment ---
if [[ ! "$ENVIRONMENT" =~ ^(dev|test|prod)$ ]]; then
    echo "❌ Invalid environment: $ENVIRONMENT (must be dev, test, or prod)"
    exit 1
fi

# --- Auto-detect hosting mode from .env.azure if not provided ---
ENV_AZURE_FILE="$REPO_ROOT/.env.azure"
if [[ -z "$HOSTING_MODE" ]]; then
    if [[ -f "$ENV_AZURE_FILE" ]]; then
        HOSTING_MODE=$(grep -E '^HOSTING_MODE=' "$ENV_AZURE_FILE" | cut -d'=' -f2 | tr -d '[:space:]' || echo "")
    fi
    HOSTING_MODE="${HOSTING_MODE:-none}"
fi

# --- Validate hosting mode ---
if [[ ! "$HOSTING_MODE" =~ ^(none|appService|aca)$ ]]; then
    echo "❌ Invalid hosting mode: $HOSTING_MODE (must be none, appService, or aca)"
    exit 1
fi

echo "=============================================="
echo "  Salesforce AI Assistant — App Deployment"
echo "=============================================="
echo "  Environment:   $ENVIRONMENT"
echo "  Hosting Mode:  $HOSTING_MODE"
echo "=============================================="
echo ""

# --- Derive resource names (read from .env.azure or env var) ---
if [[ -z "${AZURE_PROJECT_NAME:-}" && -f "$ENV_AZURE_FILE" ]]; then
    AZURE_PROJECT_NAME=$(grep -E '^AZURE_PROJECT_NAME=' "$ENV_AZURE_FILE" | cut -d'=' -f2 | tr -d '[:space:]' || echo "")
fi
PROJECT_NAME="${AZURE_PROJECT_NAME:-sfai-${ENVIRONMENT}}"
RESOURCE_GROUP="rg-${PROJECT_NAME}"

# =============================================================================
# Hosting Mode: none
# =============================================================================
if [[ "$HOSTING_MODE" == "none" ]]; then
    echo "ℹ️  Hosting mode is 'none' — no deployment needed."
    echo "   MCP servers run locally via stdio transport (notebook mode)."
    exit 0
fi

# =============================================================================
# Hosting Mode: appService
# =============================================================================
deploy_app_service() {
    echo "📦 Deploying to Azure App Service..."

    local CRM_APP="app-${PROJECT_NAME}-crm"
    local KB_APP="app-${PROJECT_NAME}-knowledge"

    # Create deployment zip (excluding unnecessary files)
    local ZIP_FILE
    ZIP_FILE=$(mktemp /tmp/sfai-deploy-XXXXXX.zip)
    echo "  Creating deployment package..."
    cd "$REPO_ROOT"
    zip -r "$ZIP_FILE" \
        requirements.txt \
        shared/ \
        config/ \
        mcp_servers/ \
        -x '*/__pycache__/*' '*.pyc' '*.pyo' '.env*' \
        > /dev/null

    echo "  Deploying CRM MCP server → $CRM_APP..."
    az webapp deploy \
        --name "$CRM_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --src-path "$ZIP_FILE" \
        --type zip \
        --async true

    echo "  Deploying Knowledge MCP server → $KB_APP..."
    az webapp deploy \
        --name "$KB_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --src-path "$ZIP_FILE" \
        --type zip \
        --async true

    rm -f "$ZIP_FILE"
    echo "✅ App Service deployment complete"
}

# =============================================================================
# Hosting Mode: aca
# =============================================================================
deploy_aca() {
    echo "🐳 Deploying to Azure Container Apps..."

    # Resolve ACR login server
    local ACR_LOGIN_SERVER
    if [[ -f "$ENV_AZURE_FILE" ]]; then
        ACR_LOGIN_SERVER=$(grep -E '^ACR_LOGIN_SERVER=' "$ENV_AZURE_FILE" | cut -d'=' -f2 | tr -d '[:space:]' || echo "")
    fi
    ACR_LOGIN_SERVER="${ACR_LOGIN_SERVER:-${ACR_NAME:-crsfai${ENVIRONMENT}}.azurecr.io}"

    local IMAGE_TAG
    IMAGE_TAG=$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo "latest")

    local CRM_IMAGE="${ACR_LOGIN_SERVER}/sfai-crm:${IMAGE_TAG}"
    local KB_IMAGE="${ACR_LOGIN_SERVER}/sfai-knowledge:${IMAGE_TAG}"

    local CRM_APP="ca-${PROJECT_NAME}-crm"
    local KB_APP="ca-${PROJECT_NAME}-knowledge"

    # Step 1: Log in to ACR
    echo "  Authenticating with ACR: ${ACR_LOGIN_SERVER}..."
    az acr login --name "${ACR_LOGIN_SERVER%%.*}"

    # Step 2: Build CRM server image (ACA requires linux/amd64)
    echo "  Building CRM server image → ${CRM_IMAGE}..."
    docker build \
        --platform linux/amd64 \
        --target crm-server \
        -t "$CRM_IMAGE" \
        "$REPO_ROOT"

    # Step 3: Build Knowledge server image
    echo "  Building Knowledge server image → ${KB_IMAGE}..."
    docker build \
        --platform linux/amd64 \
        --target knowledge-server \
        -t "$KB_IMAGE" \
        "$REPO_ROOT"

    # Step 4: Push images
    echo "  Pushing CRM image..."
    docker push "$CRM_IMAGE"

    echo "  Pushing Knowledge image..."
    docker push "$KB_IMAGE"

    # Step 5: Configure ACR registry on container apps (needed when switching from placeholder)
    echo "  Configuring ACR registry on container apps..."
    az containerapp registry set \
        --name "$CRM_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --server "$ACR_LOGIN_SERVER" \
        --identity system

    az containerapp registry set \
        --name "$KB_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --server "$ACR_LOGIN_SERVER" \
        --identity system

    # Step 6: Update container apps with real images and correct port
    echo "  Updating CRM Container App → $CRM_APP..."
    az containerapp update \
        --name "$CRM_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --image "$CRM_IMAGE" \
        --set-env-vars "FASTMCP_PORT=8000"

    az containerapp ingress update \
        --name "$CRM_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --target-port 8000

    echo "  Updating Knowledge Container App → $KB_APP..."
    az containerapp update \
        --name "$KB_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --image "$KB_IMAGE" \
        --set-env-vars "FASTMCP_PORT=8000"

    az containerapp ingress update \
        --name "$KB_APP" \
        --resource-group "$RESOURCE_GROUP" \
        --target-port 8000

    echo "✅ ACA deployment complete"
    echo "  CRM:       https://$(az containerapp show --name "$CRM_APP" --resource-group "$RESOURCE_GROUP" --query 'properties.configuration.ingress.fqdn' -o tsv)"
    echo "  Knowledge: https://$(az containerapp show --name "$KB_APP" --resource-group "$RESOURCE_GROUP" --query 'properties.configuration.ingress.fqdn' -o tsv)"
}

# =============================================================================
# Route to the correct deployment function
# =============================================================================
case "$HOSTING_MODE" in
    appService) deploy_app_service ;;
    aca)        deploy_aca ;;
    *)          echo "❌ Unexpected hosting mode: $HOSTING_MODE"; exit 1 ;;
esac

echo ""
echo "=============================================="
echo "  Deployment complete!"
echo "=============================================="
