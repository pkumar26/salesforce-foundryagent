# =============================================================================
# Dockerfile — Multi-stage build for MCP servers (ACA deployment)
# Usage:
#   docker build --target crm-server -t sfai-crm:latest .
#   docker build --target knowledge-server -t sfai-knowledge:latest .
# =============================================================================

# --- Base stage: shared dependencies ---
FROM python:3.11-slim AS base

WORKDIR /app

# Install dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules and config
COPY shared/ shared/
COPY config/ config/

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser

# --- CRM MCP Server ---
FROM base AS crm-server

COPY mcp_servers/__init__.py mcp_servers/__init__.py
COPY mcp_servers/salesforce_crm/ mcp_servers/salesforce_crm/

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "mcp_servers.salesforce_crm.server"]

# --- Knowledge MCP Server ---
FROM base AS knowledge-server

COPY mcp_servers/__init__.py mcp_servers/__init__.py
COPY mcp_servers/salesforce_knowledge/ mcp_servers/salesforce_knowledge/

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "mcp_servers.salesforce_knowledge.server"]
