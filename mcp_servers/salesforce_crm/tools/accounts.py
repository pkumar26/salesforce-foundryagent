"""Account tools for the Salesforce CRM MCP Server.

Implements: get_account, search_accounts
Contract: contracts/mcp-salesforce-crm.md
"""

from __future__ import annotations

import logging
from typing import Any

from mcp_servers.salesforce_crm.server import _get_sf_client, mcp
from shared.models import AccountSummary, ErrorResponse
from shared.salesforce_client import SalesforceClientError

logger = logging.getLogger(__name__)


def _record_to_account(record: dict[str, Any]) -> AccountSummary:
    """Transform a Salesforce Account record to AccountSummary."""
    owner = record.get("Owner") or {}
    return AccountSummary(
        id=record["Id"],
        name=record["Name"],
        industry=record.get("Industry"),
        type=record.get("Type"),
        annual_revenue=record.get("AnnualRevenue"),
        billing_city=record.get("BillingCity"),
        billing_state=record.get("BillingState"),
        owner_name=owner.get("Name") if isinstance(owner, dict) else None,
        description=record.get("Description"),
    )


ACCOUNT_FIELDS = (
    "Id, Name, Industry, Type, AnnualRevenue, "
    "BillingCity, BillingState, Owner.Name, Description"
)


@mcp.tool()
def get_account(
    account_id: str | None = None,
    account_name: str | None = None,
) -> dict[str, Any]:
    """Retrieve account details by Salesforce ID or account name.

    Args:
        account_id: Salesforce Account ID (18-char). If provided, exact lookup.
        account_name: Account name for fuzzy search. Used when account_id is not provided.
    """
    if not account_id and not account_name:
        return ErrorResponse(
            code="INVALID_INPUT",
            message="Either account_id or account_name is required.",
        ).model_dump()

    try:
        sf = _get_sf_client()

        if account_id:
            # Exact lookup by ID
            soql = f"SELECT {ACCOUNT_FIELDS} FROM Account WHERE Id = '{account_id}' LIMIT 1"
            records = sf.query(soql)
            if not records:
                return ErrorResponse(
                    code="NOT_FOUND",
                    message=f"Account with ID '{account_id}' not found.",
                ).model_dump()
            account = _record_to_account(records[0])
            return {"account": account.model_dump(), "match_count": 1, "matches": []}

        # Fuzzy search by name
        safe_name = account_name.replace("'", "\\'") if account_name else ""
        soql = (
            f"SELECT {ACCOUNT_FIELDS} FROM Account "
            f"WHERE Name LIKE '%{safe_name}%' LIMIT 5"
        )
        records = sf.query(soql)

        if not records:
            return ErrorResponse(
                code="NOT_FOUND",
                message=f"No accounts found matching '{account_name}'.",
            ).model_dump()

        if len(records) == 1:
            account = _record_to_account(records[0])
            return {"account": account.model_dump(), "match_count": 1, "matches": []}

        # Multiple matches — disambiguation
        matches = [{"id": r["Id"], "name": r["Name"]} for r in records]
        return {
            "account": None,
            "match_count": len(matches),
            "matches": matches,
        }

    except SalesforceClientError as e:
        return e.to_error_response()


@mcp.tool()
def search_accounts(
    query: str,
    industry: str | None = None,
    owner_id: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """Search accounts by name, industry, or owner with pagination.

    Args:
        query: Search term for account name (LIKE match).
        industry: Filter by industry picklist value.
        owner_id: Filter by account owner's Salesforce User ID.
        limit: Maximum results to return (1-50, default 25).
    """
    limit = max(1, min(50, limit))

    try:
        sf = _get_sf_client()

        safe_query = query.replace("'", "\\'")
        conditions = [f"Name LIKE '%{safe_query}%'"]

        if industry:
            safe_industry = industry.replace("'", "\\'")
            conditions.append(f"Industry = '{safe_industry}'")

        if owner_id:
            conditions.append(f"OwnerId = '{owner_id}'")

        where_clause = " AND ".join(conditions)
        soql = (
            f"SELECT {ACCOUNT_FIELDS} FROM Account "
            f"WHERE {where_clause} ORDER BY Name ASC LIMIT {limit + 1}"
        )
        records = sf.query(soql)

        has_more = len(records) > limit
        if has_more:
            records = records[:limit]

        accounts = [_record_to_account(r).model_dump() for r in records]

        return {
            "accounts": accounts,
            "total_count": len(accounts),
            "has_more": has_more,
        }

    except SalesforceClientError as e:
        return e.to_error_response()
