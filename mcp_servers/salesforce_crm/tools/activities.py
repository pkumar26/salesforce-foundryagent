"""Activity tools for the Salesforce CRM MCP Server.

Implements: get_recent_activities, create_task
Contract: contracts/mcp-salesforce-crm.md
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from mcp_servers.salesforce_crm.server import _get_sf_client, mcp
from shared.models import ActivitySummary
from shared.salesforce_client import SalesforceClientError, WriteBackConfirmationRequired

logger = logging.getLogger(__name__)


TASK_FIELDS = "Id, Subject, ActivityDate, Status, Owner.Name"
EVENT_FIELDS = "Id, Subject, ActivityDate, Owner.Name"


def _record_to_activity(record: dict[str, Any], activity_type: str) -> ActivitySummary:
    """Transform a Salesforce Task/Event record to ActivitySummary."""
    owner = record.get("Owner") or {}
    return ActivitySummary(
        id=record["Id"],
        type=activity_type,
        subject=record.get("Subject", ""),
        date=date.fromisoformat(record["ActivityDate"]) if record.get("ActivityDate") else None,
        status=record.get("Status") if activity_type == "Task" else None,
        owner_name=owner.get("Name") if isinstance(owner, dict) else None,
    )


@mcp.tool()
def get_recent_activities(
    related_to_id: str,
    days: int = 30,
    limit: int = 25,
) -> dict[str, Any]:
    """List recent tasks and events for an account, contact, or opportunity.

    Args:
        related_to_id: Account, Contact, or Opportunity ID.
        days: Look back N days (1-90, default 30).
        limit: Maximum results to return (1-50, default 25).
    """
    days = max(1, min(90, days))
    limit = max(1, min(50, limit))
    cutoff_date = (date.today() - timedelta(days=days)).isoformat()

    try:
        sf = _get_sf_client()
        activities: list[dict[str, Any]] = []

        # Query Tasks
        task_soql = (
            f"SELECT {TASK_FIELDS} FROM Task "
            f"WHERE (WhatId = '{related_to_id}' OR WhoId = '{related_to_id}') "
            f"AND ActivityDate >= {cutoff_date} "
            f"ORDER BY ActivityDate DESC LIMIT {limit}"
        )
        try:
            task_records = sf.query(task_soql)
            for r in task_records:
                activities.append(_record_to_activity(r, "Task").model_dump())
        except SalesforceClientError:
            logger.debug("Unable to query tasks for %s", related_to_id)

        # Query Events
        remaining = limit - len(activities)
        if remaining > 0:
            event_soql = (
                f"SELECT {EVENT_FIELDS} FROM Event "
                f"WHERE (WhatId = '{related_to_id}' OR WhoId = '{related_to_id}') "
                f"AND ActivityDate >= {cutoff_date} "
                f"ORDER BY ActivityDate DESC LIMIT {remaining}"
            )
            try:
                event_records = sf.query(event_soql)
                for r in event_records:
                    activities.append(_record_to_activity(r, "Event").model_dump())
            except SalesforceClientError:
                logger.debug("Unable to query events for %s", related_to_id)

        # Sort by date descending
        activities.sort(
            key=lambda a: a.get("date") or "0000-00-00",
            reverse=True,
        )

        return {
            "activities": activities[:limit],
            "total_count": len(activities),
        }

    except SalesforceClientError as e:
        return e.to_error_response()


@mcp.tool()
def create_task(
    subject: str,
    description: str | None = None,
    due_date: str | None = None,
    related_to_id: str | None = None,
    who_id: str | None = None,
    priority: str = "Normal",
    confirmed: bool = False,
) -> dict[str, Any]:
    """Log a new task in Salesforce. Requires user confirmation.

    Args:
        subject: Task subject.
        description: Task description.
        due_date: Due date (YYYY-MM-DD).
        related_to_id: Account or Opportunity ID (WhatId).
        who_id: Contact or Lead ID (WhoId).
        priority: Priority level: High, Normal, or Low (default Normal).
        confirmed: Whether the user has confirmed this write operation.
    """
    try:
        sf = _get_sf_client()

        task_data: dict[str, Any] = {
            "Subject": subject,
            "Priority": priority,
            "Status": "Not Started",
        }

        if description:
            task_data["Description"] = description
        if due_date:
            task_data["ActivityDate"] = due_date
        if related_to_id:
            task_data["WhatId"] = related_to_id
        if who_id:
            task_data["WhoId"] = who_id

        result = sf.create_record("Task", task_data, confirmed=confirmed)

        return {
            "task_id": result.get("id", ""),
            "success": result.get("success", True),
            "message": f"Task '{subject}' created successfully.",
        }

    except WriteBackConfirmationRequired:
        return {
            "task_id": None,
            "success": False,
            "message": (
                f"Please confirm: Create task '{subject}' "
                f"with priority '{priority}'"
                + (f", due {due_date}" if due_date else "")
                + "? Call again with confirmed=true to proceed."
            ),
        }

    except SalesforceClientError as e:
        return e.to_error_response()
