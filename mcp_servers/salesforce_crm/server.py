"""Salesforce CRM MCP Server — FastMCP server with 15 CRM data tools.

Entry point for the salesforce-crm MCP server.
Transport: stdio (notebooks) / SSE (hosted deployment).
"""

from __future__ import annotations

import logging
import os

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Create the FastMCP server instance
mcp = FastMCP(
    "salesforce-crm",
    host=os.environ.get("FASTMCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("FASTMCP_PORT", "8000")),
)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):  # noqa: ARG001
    """Health-check endpoint for container orchestrators."""
    from starlette.responses import JSONResponse

    return JSONResponse({"status": "ok", "server": "salesforce-crm"})

# Tool registration imports — must come AFTER mcp is defined
# Each module uses the @mcp.tool() decorator to self-register
def _register_tools() -> None:
    """Import tool modules to trigger registration."""
    import mcp_servers.salesforce_crm.tools.accounts  # noqa: F401
    import mcp_servers.salesforce_crm.tools.activities  # noqa: F401
    import mcp_servers.salesforce_crm.tools.cases  # noqa: F401
    import mcp_servers.salesforce_crm.tools.contacts  # noqa: F401
    import mcp_servers.salesforce_crm.tools.leads  # noqa: F401
    import mcp_servers.salesforce_crm.tools.opportunities  # noqa: F401
    import mcp_servers.salesforce_crm.tools.users  # noqa: F401


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


# Tool registrations will be added as tools are implemented in tools/ modules.
# Each tool module registers its tools by importing the `mcp` instance.


if __name__ == "__main__":
    import sys as _sys

    # Prevent double-import: when tool modules do
    # ``from mcp_servers.salesforce_crm.server import mcp`` they must get
    # *this* module's ``mcp`` instance, not a second copy.
    _sys.modules.setdefault("mcp_servers.salesforce_crm.server", _sys.modules[__name__])

    from shared.telemetry import setup_telemetry

    setup_telemetry("salesforce-crm")
    _register_tools()
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
