"""Contact tools for the Salesforce CRM MCP Server.

Implements: get_contacts_for_account
Contract: contracts/mcp-salesforce-crm.md
"""

from __future__ import annotations

import logging
from typing import Any

from mcp_servers.salesforce_crm.server import _get_sf_client, mcp
from shared.models import ContactSummary
from shared.salesforce_client import SalesforceClientError

logger = logging.getLogger(__name__)


CONTACT_FIELDS = "Id, Name, Title, Email, Phone"


def _record_to_contact(record: dict[str, Any], role: str | None = None) -> ContactSummary:
    """Transform a Salesforce Contact record to ContactSummary."""
    return ContactSummary(
        id=record["Id"],
        name=record["Name"],
        title=record.get("Title"),
        email=record.get("Email"),
        phone=record.get("Phone"),
        role=role,
    )


@mcp.tool()
def get_contacts_for_account(
    account_id: str,
    limit: int = 25,
) -> dict[str, Any]:
    """List contacts for a given account, including opportunity contact roles.

    Args:
        account_id: Salesforce Account ID.
        limit: Maximum results to return (1-50, default 25).
    """
    limit = max(1, min(50, limit))

    try:
        sf = _get_sf_client()

        # Get contacts for the account
        soql = (
            f"SELECT {CONTACT_FIELDS} FROM Contact "
            f"WHERE AccountId = '{account_id}' "
            f"ORDER BY Name ASC LIMIT {limit}"
        )
        records = sf.query(soql)

        # Get opportunity contact roles for these contacts
        contact_ids = [r["Id"] for r in records]
        roles_map: dict[str, str] = {}

        if contact_ids:
            ids_clause = "', '".join(contact_ids)
            roles_soql = (
                f"SELECT ContactId, Role FROM OpportunityContactRole "
                f"WHERE ContactId IN ('{ids_clause}') "
                f"AND Opportunity.IsClosed = false"
            )
            try:
                role_records = sf.query(roles_soql)
                for rr in role_records:
                    cid = rr.get("ContactId", "")
                    role = rr.get("Role")
                    if cid and role and cid not in roles_map:
                        # Keep first role found (primary)
                        roles_map[cid] = role
            except SalesforceClientError:
                # OpportunityContactRole may not be accessible; continue without roles
                logger.debug("Unable to retrieve contact roles, continuing without them")

        contacts = [
            _record_to_contact(r, roles_map.get(r["Id"])).model_dump()
            for r in records
        ]

        return {
            "contacts": contacts,
            "total_count": len(contacts),
        }

    except SalesforceClientError as e:
        return e.to_error_response()
