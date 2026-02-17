"""Lead tools for the Salesforce CRM MCP Server.

Implements: get_leads, update_lead_status
Contract: contracts/mcp-salesforce-crm.md
"""

from __future__ import annotations

import logging
from typing import Any

from mcp_servers.salesforce_crm.server import _get_sf_client, mcp
from shared.models import ErrorResponse, LeadSummary
from shared.salesforce_client import SalesforceClientError, WriteBackConfirmationRequired

logger = logging.getLogger(__name__)


LEAD_FIELDS = (
    "Id, FirstName, LastName, Company, Title, Email, Phone, "
    "Status, LeadSource, Owner.Name, CreatedDate"
)


def _record_to_lead(record: dict[str, Any]) -> LeadSummary:
    """Transform a Salesforce Lead record to LeadSummary."""
    owner = record.get("Owner") or {}
    return LeadSummary(
        id=record["Id"],
        first_name=record.get("FirstName", ""),
        last_name=record.get("LastName", ""),
        company=record.get("Company", ""),
        title=record.get("Title"),
        email=record.get("Email"),
        phone=record.get("Phone"),
        status=record.get("Status", ""),
        lead_source=record.get("LeadSource"),
        owner_name=owner.get("Name") if isinstance(owner, dict) else None,
    )


@mcp.tool()
def get_leads(
    owner_id: str | None = None,
    status: str | None = None,
    lead_source: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """List leads with optional filters for owner, status, and source.

    Args:
        owner_id: Filter by lead owner User ID.
        status: Filter by lead status (e.g., 'Open - Not Contacted', 'Working').
        lead_source: Filter by lead source (e.g., 'Web', 'Referral').
        limit: Maximum results to return (1-50, default 25).
    """
    limit = max(1, min(50, limit))

    try:
        sf = _get_sf_client()

        conditions: list[str] = ["IsConverted = false"]
        if owner_id:
            conditions.append(f"OwnerId = '{owner_id}'")
        if status:
            safe_status = status.replace("'", "\\'")
            conditions.append(f"Status = '{safe_status}'")
        if lead_source:
            safe_source = lead_source.replace("'", "\\'")
            conditions.append(f"LeadSource = '{safe_source}'")

        where_clause = " AND ".join(conditions)
        soql = (
            f"SELECT {LEAD_FIELDS} FROM Lead "
            f"WHERE {where_clause} "
            f"ORDER BY CreatedDate DESC LIMIT {limit}"
        )
        records = sf.query(soql)
        leads = [_record_to_lead(r).model_dump() for r in records]

        return {
            "leads": leads,
            "total_count": len(leads),
        }

    except SalesforceClientError as e:
        return e.to_error_response()


@mcp.tool()
def update_lead_status(
    lead_id: str,
    status: str,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Update the status of a lead. Requires user confirmation.

    Args:
        lead_id: Salesforce Lead ID.
        status: New status value (e.g., 'Working', 'Qualified', 'Unqualified').
        confirmed: Whether the user has confirmed this write operation.
    """
    try:
        sf = _get_sf_client()
        sf.update_record("Lead", lead_id, {"Status": status}, confirmed=confirmed)

        return {
            "success": True,
            "message": f"Lead {lead_id} status updated to '{status}'.",
            "updated_fields": ["Status"],
        }

    except WriteBackConfirmationRequired:
        return {
            "success": False,
            "message": (
                f"Please confirm: Update lead {lead_id} status to '{status}'? "
                f"Call again with confirmed=true to proceed."
            ),
            "updated_fields": [],
        }

    except SalesforceClientError as e:
        return e.to_error_response()
