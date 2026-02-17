"""User (team member) tools for the Salesforce CRM MCP Server.

Implements: get_team_members
Contract: contracts/mcp-salesforce-crm.md
"""

from __future__ import annotations

import logging
from typing import Any

from mcp_servers.salesforce_crm.server import _get_sf_client, mcp
from shared.models import TeamMember
from shared.salesforce_client import SalesforceClientError

logger = logging.getLogger(__name__)


USER_FIELDS = "Id, Name, IsActive, Profile.Name"


def _record_to_team_member(record: dict[str, Any]) -> TeamMember:
    """Transform a Salesforce User record to TeamMember."""
    profile = record.get("Profile") or {}
    return TeamMember(
        id=record["Id"],
        name=record["Name"],
        is_active=record.get("IsActive", True),
        profile_name=profile.get("Name") if isinstance(profile, dict) else None,
    )


@mcp.tool()
def get_team_members(
    manager_id: str,
) -> dict[str, Any]:
    """List active users reporting to a given manager.

    Args:
        manager_id: Manager's Salesforce User ID.
    """
    try:
        sf = _get_sf_client()

        soql = (
            f"SELECT {USER_FIELDS} FROM User "
            f"WHERE ManagerId = '{manager_id}' AND IsActive = true "
            f"ORDER BY Name ASC"
        )
        records = sf.query(soql)

        team_members = [_record_to_team_member(r).model_dump() for r in records]

        return {
            "team_members": team_members,
            "count": len(team_members),
        }

    except SalesforceClientError as e:
        return e.to_error_response()
