"""Salesforce Knowledge MCP Server — FastMCP server with 2 Knowledge Article tools.

Entry point for the salesforce-knowledge MCP server.
Transport: stdio (notebooks) / SSE (hosted deployment).
"""

from __future__ import annotations

import logging
import os

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Create the FastMCP server instance
mcp = FastMCP(
    "salesforce-knowledge",
    host=os.environ.get("FASTMCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("FASTMCP_PORT", "8000")),
)


def _get_sf_client():
    """Get a SalesforceClient instance from environment variables."""
    from shared.salesforce_client import SalesforceClient

    instance_url = os.environ.get("SF_INSTANCE_URL", "")
    access_token = os.environ.get("SF_ACCESS_TOKEN", "")

    if not instance_url or not access_token:
        raise RuntimeError(
            "SF_INSTANCE_URL and SF_ACCESS_TOKEN environment variables are required."
        )

    return SalesforceClient(instance_url=instance_url, access_token=access_token)


# Tool registration imports — must come AFTER mcp is defined
def _register_tools() -> None:
    """Import tool modules to trigger registration."""
    import mcp_servers.salesforce_knowledge.tools.articles  # noqa: F401


if __name__ == "__main__":
    import sys as _sys

    # Prevent double-import: when tool modules do
    # ``from mcp_servers.salesforce_knowledge.server import mcp`` they must get
    # *this* module's ``mcp`` instance, not a second copy.
    _sys.modules.setdefault("mcp_servers.salesforce_knowledge.server", _sys.modules[__name__])

    from shared.telemetry import setup_telemetry

    setup_telemetry("salesforce-knowledge")
    _register_tools()
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
