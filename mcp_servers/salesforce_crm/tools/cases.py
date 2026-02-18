"""Case tools for the Salesforce CRM MCP Server.

Implements: get_case, create_case, update_case
Contract: contracts/mcp-salesforce-crm.md
"""

from __future__ import annotations

import logging
from datetime import UTC
from typing import Any

from mcp_servers.salesforce_crm.server import _get_sf_client, mcp
from shared.models import CaseSummary, ErrorResponse
from shared.salesforce_client import SalesforceClientError, WriteBackConfirmationError

logger = logging.getLogger(__name__)


CASE_FIELDS = (
    "Id, CaseNumber, Subject, Description, Status, Priority, Type, "
    "CreatedDate, Owner.Name, Account.Name"
)


def _record_to_case(record: dict[str, Any]) -> CaseSummary:
    """Transform a Salesforce Case record to CaseSummary."""
    owner = record.get("Owner") or {}
    account = record.get("Account") or {}
    return CaseSummary(
        id=record["Id"],
        case_number=record.get("CaseNumber", ""),
        subject=record.get("Subject", ""),
        description=record.get("Description"),
        status=record.get("Status", ""),
        priority=record.get("Priority", ""),
        type=record.get("Type"),
        created_date=record.get("CreatedDate", ""),
        owner_name=owner.get("Name") if isinstance(owner, dict) else None,
        account_name=account.get("Name") if isinstance(account, dict) else None,
        recent_comments=[],
    )


@mcp.tool()
def get_case(
    case_id: str | None = None,
    case_number: str | None = None,
) -> dict[str, Any]:
    """Retrieve case details by Salesforce Case ID or case number.

    Args:
        case_id: Salesforce Case ID (18-char).
        case_number: Case number (e.g., '00012345'). Used when case_id not provided.
    """
    if not case_id and not case_number:
        return ErrorResponse(
            code="INVALID_INPUT",
            message="Either case_id or case_number is required.",
        ).model_dump()

    try:
        sf = _get_sf_client()

        if case_id:
            soql = f"SELECT {CASE_FIELDS} FROM Case WHERE Id = '{case_id}' LIMIT 1"
        else:
            safe_number = (case_number or "").replace("'", "\\'")
            soql = f"SELECT {CASE_FIELDS} FROM Case WHERE CaseNumber = '{safe_number}' LIMIT 1"

        records = sf.query(soql)
        if not records:
            identifier = case_id or case_number
            return ErrorResponse(
                code="NOT_FOUND",
                message=f"Case '{identifier}' not found.",
            ).model_dump()

        case = _record_to_case(records[0])

        # Fetch recent case comments
        try:
            comments_soql = (
                f"SELECT CommentBody FROM CaseComment "
                f"WHERE ParentId = '{records[0]['Id']}' "
                f"ORDER BY CreatedDate DESC LIMIT 5"
            )
            comment_records = sf.query(comments_soql)
            case.recent_comments = [
                c.get("CommentBody", "") for c in comment_records if c.get("CommentBody")
            ]
        except SalesforceClientError:
            logger.debug("Unable to fetch case comments")

        return {"case": case.model_dump()}

    except SalesforceClientError as e:
        return e.to_error_response()


@mcp.tool()
def create_case(
    subject: str,
    description: str,
    priority: str = "Medium",
    case_type: str | None = None,
    account_id: str | None = None,
    contact_id: str | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Create a new Salesforce case. Requires user confirmation before execution.

    Args:
        subject: Case subject line.
        description: Detailed case description.
        priority: Priority level: High, Medium, or Low (default Medium).
        case_type: Case type/category.
        account_id: Related account ID.
        contact_id: Related contact ID.
        confirmed: Whether the user has confirmed this write operation.
    """
    try:
        sf = _get_sf_client()

        case_data: dict[str, Any] = {
            "Subject": subject,
            "Description": description,
            "Priority": priority,
        }
        if case_type:
            case_data["Type"] = case_type
        if account_id:
            case_data["AccountId"] = account_id
        if contact_id:
            case_data["ContactId"] = contact_id

        result = sf.create_record("Case", case_data, confirmed=confirmed)

        return {
            "case_id": result.get("id", ""),
            "case_number": "",  # Number is auto-generated, retrieve if needed
            "success": result.get("success", True),
            "message": f"Case '{subject}' created successfully.",
        }

    except WriteBackConfirmationError:
        return {
            "case_id": None,
            "case_number": None,
            "success": False,
            "message": (
                f"Please confirm: Create case with subject '{subject}', "
                f"priority '{priority}'"
                + (f", type '{case_type}'" if case_type else "")
                + "? Call again with confirmed=true to proceed."
            ),
        }

    except SalesforceClientError as e:
        return e.to_error_response()


@mcp.tool()
def update_case(
    case_id: str,
    priority: str | None = None,
    status: str | None = None,
    case_type: str | None = None,
    comment: str | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Update case fields and/or add an internal comment. Requires user confirmation.

    Args:
        case_id: Salesforce Case ID to update.
        priority: New priority: High, Medium, or Low.
        status: New status value.
        case_type: New type/category value.
        comment: Internal comment to add to the case.
        confirmed: Whether the user has confirmed this write operation.
    """
    update_data: dict[str, Any] = {}
    updated_fields: list[str] = []

    if priority:
        update_data["Priority"] = priority
        updated_fields.append("Priority")
    if status:
        update_data["Status"] = status
        updated_fields.append("Status")
    if case_type:
        update_data["Type"] = case_type
        updated_fields.append("Type")

    if not update_data and not comment:
        return ErrorResponse(
            code="INVALID_INPUT",
            message="At least one field to update or a comment is required.",
        ).model_dump()

    try:
        sf = _get_sf_client()

        # Update case fields
        if update_data:
            sf.update_record("Case", case_id, update_data, confirmed=confirmed)

        # Add comment if provided
        if comment:
            sf.create_record(
                "CaseComment",
                {"ParentId": case_id, "CommentBody": comment},
                confirmed=confirmed,
            )
            updated_fields.append("Comment")

        return {
            "success": True,
            "message": f"Case {case_id} updated successfully.",
            "updated_fields": updated_fields,
        }

    except WriteBackConfirmationError:
        changes_desc = ", ".join(
            f"{k}='{v}'" for k, v in update_data.items()
        )
        if comment:
            changes_desc += f", comment='{comment[:50]}...'" if len(comment or "") > 50 else f", comment='{comment}'"
        return {
            "success": False,
            "message": (
                f"Please confirm: Update case {case_id} with {changes_desc}? "
                f"Call again with confirmed=true to proceed."
            ),
            "updated_fields": [],
        }

    except SalesforceClientError as e:
        return e.to_error_response()


@mcp.tool()
def get_case_queue_summary(
    owner_id: str | None = None,
    queue_name: str | None = None,
) -> dict[str, Any]:
    """Get case queue status with counts by status/priority and aging distribution.

    Args:
        owner_id: Filter by case owner User ID.
        queue_name: Filter by queue name (e.g. 'Tier 1 Support').
    """
    try:
        sf = _get_sf_client()

        conditions = ["IsClosed = false"]
        if owner_id:
            conditions.append(f"OwnerId = '{owner_id}'")
        if queue_name:
            safe_name = queue_name.replace("'", "\\'")
            conditions.append(f"Owner.Name = '{safe_name}'")

        where_clause = " AND ".join(conditions)
        soql = (
            f"SELECT Id, Status, Priority, CreatedDate, Owner.Name "
            f"FROM Case WHERE {where_clause} "
            f"ORDER BY CreatedDate ASC LIMIT 500"
        )
        records = sf.query(soql)

        from datetime import datetime

        now = datetime.now(UTC)

        # Aggregate by status
        by_status: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        aging_buckets: dict[str, int] = {
            "0-24h": 0,
            "1-3d": 0,
            "3-7d": 0,
            "7-14d": 0,
            "14d+": 0,
        }

        for record in records:
            status = record.get("Status", "Unknown")
            priority = record.get("Priority", "Unknown")
            by_status[status] = by_status.get(status, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1

            # Calculate aging
            created_str = record.get("CreatedDate", "")
            if created_str:
                try:
                    created = datetime.fromisoformat(created_str.replace("+0000", "+00:00"))
                    age_hours = (now - created).total_seconds() / 3600
                    if age_hours <= 24:
                        aging_buckets["0-24h"] += 1
                    elif age_hours <= 72:
                        aging_buckets["1-3d"] += 1
                    elif age_hours <= 168:
                        aging_buckets["3-7d"] += 1
                    elif age_hours <= 336:
                        aging_buckets["7-14d"] += 1
                    else:
                        aging_buckets["14d+"] += 1
                except (ValueError, TypeError):
                    aging_buckets["14d+"] += 1

        # SLA compliance (cases older than 14 days are SLA breaches)
        sla_breached = aging_buckets.get("14d+", 0)
        total = len(records)
        sla_compliance_pct = (
            round((total - sla_breached) / total * 100, 1) if total > 0 else 100.0
        )

        return {
            "total_open": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "aging_distribution": aging_buckets,
            "sla_compliance_pct": sla_compliance_pct,
            "sla_breached_count": sla_breached,
        }

    except SalesforceClientError as e:
        return e.to_error_response()
