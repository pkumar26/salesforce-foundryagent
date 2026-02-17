"""Telemetry module for Application Insights integration.

Provides OpenTelemetry-based instrumentation for MCP servers.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_tracer = None
_meter = None


def setup_telemetry(service_name: str) -> None:
    """Initialize Application Insights telemetry if connection string is available.

    Args:
        service_name: Name of the MCP server for telemetry identification.
    """
    global _tracer, _meter

    connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not connection_string:
        logger.info("APPLICATIONINSIGHTS_CONNECTION_STRING not set — telemetry disabled")
        return

    try:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            connection_string=connection_string,
            service_name=service_name,
        )

        from opentelemetry import metrics, trace

        _tracer = trace.get_tracer(service_name)
        _meter = metrics.get_meter(service_name)

        logger.info("Application Insights telemetry configured for %s", service_name)

    except ImportError:
        logger.warning(
            "azure-monitor-opentelemetry not installed — telemetry disabled. "
            "Install with: pip install azure-monitor-opentelemetry"
        )
    except Exception:
        logger.warning("Failed to configure telemetry", exc_info=True)


def log_tool_invocation(tool_name: str, params: dict[str, Any], success: bool, duration_ms: float) -> None:
    """Log an MCP tool invocation as a custom event.

    Args:
        tool_name: Name of the MCP tool invoked.
        params: Tool parameters (sanitized — no secrets).
        success: Whether the tool call succeeded.
        duration_ms: Duration of the call in milliseconds.
    """
    if _tracer is None:
        return

    with _tracer.start_as_current_span(f"mcp.tool.{tool_name}") as span:
        span.set_attribute("mcp.tool.name", tool_name)
        span.set_attribute("mcp.tool.success", success)
        span.set_attribute("mcp.tool.duration_ms", duration_ms)
        for key, value in params.items():
            if key not in ("access_token", "password", "secret"):
                span.set_attribute(f"mcp.tool.param.{key}", str(value))


def log_write_back_audit(
    tool_name: str,
    object_type: str,
    record_id: str,
    operation: str,
    fields_written: dict[str, Any],
    user_confirmed: bool,
) -> None:
    """Log a write-back audit event to Application Insights.

    Per FR-016: All AI-initiated Salesforce write-back actions must be logged.

    Args:
        tool_name: MCP tool that initiated the write-back.
        object_type: Salesforce object type (e.g., 'Case', 'Task').
        record_id: Salesforce record ID.
        operation: 'create' or 'update'.
        fields_written: Dictionary of fields and values written.
        user_confirmed: Whether the user explicitly confirmed.
    """
    if _tracer is None:
        return

    with _tracer.start_as_current_span("mcp.writeback.audit") as span:
        span.set_attribute("writeback.tool", tool_name)
        span.set_attribute("writeback.object_type", object_type)
        span.set_attribute("writeback.record_id", record_id)
        span.set_attribute("writeback.operation", operation)
        span.set_attribute("writeback.user_confirmed", user_confirmed)
        span.set_attribute("writeback.fields", str(list(fields_written.keys())))

    logger.info(
        "Write-back audit: %s %s/%s — fields: %s, confirmed: %s",
        operation,
        object_type,
        record_id,
        list(fields_written.keys()),
        user_confirmed,
    )
