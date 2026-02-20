"""Opportunity tools for the Salesforce CRM MCP Server.

Implements: get_opportunities, get_pipeline_summary
Contract: contracts/mcp-salesforce-crm.md
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import yaml

from mcp_servers.salesforce_crm.server import _get_sf_client, mcp
from shared.models import OpportunitySummary
from shared.salesforce_client import SalesforceClientError

logger = logging.getLogger(__name__)


OPP_FIELDS = (
    "Id, Name, Amount, StageName, CloseDate, Probability, "
    "Owner.Name, Account.Name, LastActivityDate"
)


def _load_risk_thresholds() -> dict[str, Any]:
    """Load risk thresholds from config/risk_thresholds.yaml."""
    try:
        with open("config/risk_thresholds.yaml") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning("risk_thresholds.yaml not found, using defaults")
        return {
            "stage_stagnation_days": 30,
            "inactivity_days": 14,
            "low_probability_threshold": 30,
            "overdue_close_date": {"enabled": True},
            "late_stages": ["Negotiation/Review", "Proposal/Price Quote"],
            "minimum_amount_for_risk": 10000,
        }


def _record_to_opportunity(record: dict[str, Any]) -> OpportunitySummary:
    """Transform a Salesforce Opportunity record to OpportunitySummary."""
    owner = record.get("Owner") or {}
    account = record.get("Account") or {}
    close_date_str = record.get("CloseDate", "")
    last_activity_str = record.get("LastActivityDate")

    return OpportunitySummary(
        id=record["Id"],
        name=record["Name"],
        amount=record.get("Amount"),
        stage=record.get("StageName", ""),
        close_date=date.fromisoformat(close_date_str) if close_date_str else date.today(),
        probability=record.get("Probability"),
        owner_name=owner.get("Name") if isinstance(owner, dict) else None,
        account_name=account.get("Name") if isinstance(account, dict) else None,
        last_activity_date=(
            date.fromisoformat(last_activity_str) if last_activity_str else None
        ),
        risk_flags=[],
    )


def _apply_risk_flags(opp: OpportunitySummary, thresholds: dict[str, Any]) -> OpportunitySummary:
    """Apply risk flags to an opportunity based on thresholds."""
    flags: list[str] = []
    today = date.today()

    # Overdue close date
    overdue_config = thresholds.get("overdue_close_date", {})
    if overdue_config.get("enabled", True) and opp.close_date < today:
        flags.append("Overdue close date")

    # Inactivity
    inactivity_days = thresholds.get("inactivity_days", 14)
    if opp.last_activity_date:
        days_since_activity = (today - opp.last_activity_date).days
        if days_since_activity > inactivity_days:
            flags.append(f"No activity in {days_since_activity} days")
    else:
        flags.append("No recorded activity")

    # Low probability
    low_prob = thresholds.get("low_probability_threshold", 30)
    if opp.probability is not None and opp.probability < low_prob:
        flags.append(f"Low probability ({opp.probability}%)")

    # Stage stagnation — late stages approaching close
    late_stages = thresholds.get("late_stages", [])
    stagnation_days = thresholds.get("stage_stagnation_days", 30)
    if opp.stage in late_stages:
        days_to_close = (opp.close_date - today).days
        if days_to_close < stagnation_days and days_to_close > 0:
            flags.append(f"Late stage with {days_to_close} days to close")

    opp.risk_flags = flags
    return opp


@mcp.tool()
def get_opportunities(
    owner_id: str | None = None,
    account_id: str | None = None,
    stage: str | None = None,
    close_date_from: str | None = None,
    close_date_to: str | None = None,
    include_closed: bool = False,
    limit: int = 25,
) -> dict[str, Any]:
    """List open opportunities. Call with NO arguments to get all open deals.

    All parameters are optional filters.

    Args:
        owner_id: (Optional) Filter by opportunity owner User ID.
        account_id: (Optional) Filter by account ID.
        stage: (Optional) Filter by stage name.
        close_date_from: (Optional) Close date range start (YYYY-MM-DD).
        close_date_to: (Optional) Close date range end (YYYY-MM-DD).
        include_closed: Include closed deals (default False).
        limit: Maximum results to return (1-50, default 25).
    """
    limit = max(1, min(50, limit))

    try:
        sf = _get_sf_client()

        conditions: list[str] = []
        if not include_closed:
            conditions.append("IsClosed = false")

        if owner_id:
            conditions.append(f"OwnerId = '{owner_id}'")
        if account_id:
            conditions.append(f"AccountId = '{account_id}'")
        if stage:
            safe_stage = stage.replace("'", "\\'")
            conditions.append(f"StageName = '{safe_stage}'")
        if close_date_from:
            conditions.append(f"CloseDate >= {close_date_from}")
        if close_date_to:
            conditions.append(f"CloseDate <= {close_date_to}")

        where_clause = " AND ".join(conditions) if conditions else "IsClosed = false"
        soql = (
            f"SELECT {OPP_FIELDS} FROM Opportunity "
            f"WHERE {where_clause} "
            f"ORDER BY CloseDate ASC LIMIT {limit}"
        )
        records = sf.query(soql)

        opportunities = [_record_to_opportunity(r).model_dump() for r in records]
        total_value = sum(o.get("amount") or 0 for o in opportunities)

        return {
            "opportunities": opportunities,
            "total_count": len(opportunities),
            "total_value": total_value,
        }

    except SalesforceClientError as e:
        return e.to_error_response()


@mcp.tool()
def get_pipeline_summary(
    manager_id: str | None = None,
    owner_id: str | None = None,
) -> dict[str, Any]:
    """Aggregate pipeline by owner and stage with risk flags applied.

    Call with NO arguments to get a full pipeline summary across all reps.
    Both parameters are optional.

    Args:
        manager_id: (Optional) Manager User ID to scope to that manager's direct reports only.
        owner_id: (Optional) Specific owner User ID to scope to one rep's pipeline only.
    """
    try:
        sf = _get_sf_client()
        thresholds = _load_risk_thresholds()

        # Determine which owner(s) to query
        owner_ids: list[str] = []
        if owner_id:
            owner_ids = [owner_id]
        elif manager_id:
            # Get direct reports
            team_soql = (
                f"SELECT Id FROM User WHERE ManagerId = '{manager_id}' AND IsActive = true"
            )
            team_records = sf.query(team_soql)
            owner_ids = [r["Id"] for r in team_records]
            if not owner_ids:
                return {
                    "total_deals": 0,
                    "total_value": 0.0,
                    "by_stage": {},
                    "at_risk_deals": [],
                    "owner_breakdown": {},
                }

        # Build query
        conditions = ["IsClosed = false"]
        if owner_ids:
            ids_clause = "', '".join(owner_ids)
            conditions.append(f"OwnerId IN ('{ids_clause}')")

        where_clause = " AND ".join(conditions)
        soql = (
            f"SELECT {OPP_FIELDS} FROM Opportunity "
            f"WHERE {where_clause} "
            f"ORDER BY CloseDate ASC LIMIT 200"
        )
        records = sf.query(soql)

        # Transform and apply risk flags
        opps = [_record_to_opportunity(r) for r in records]
        min_amount = thresholds.get("minimum_amount_for_risk", 10000)
        for opp in opps:
            if (opp.amount or 0) >= min_amount:
                _apply_risk_flags(opp, thresholds)

        # Aggregate by stage
        by_stage: dict[str, dict[str, int | float]] = {}
        for opp in opps:
            stage_name = opp.stage
            if stage_name not in by_stage:
                by_stage[stage_name] = {"count": 0, "value": 0.0}
            by_stage[stage_name]["count"] += 1
            by_stage[stage_name]["value"] += opp.amount or 0

        # At-risk deals
        at_risk = [opp for opp in opps if opp.risk_flags]

        # Owner breakdown (when manager_id used)
        owner_breakdown: dict[str, dict[str, str | int | float]] = {}
        if manager_id:
            for opp in opps:
                oid = opp.owner_name or "Unknown"
                if oid not in owner_breakdown:
                    owner_breakdown[oid] = {
                        "owner_name": oid,
                        "deal_count": 0,
                        "total_value": 0.0,
                        "at_risk_count": 0,
                    }
                owner_breakdown[oid]["deal_count"] = int(owner_breakdown[oid]["deal_count"]) + 1
                owner_breakdown[oid]["total_value"] = float(owner_breakdown[oid]["total_value"]) + (opp.amount or 0)
                if opp.risk_flags:
                    owner_breakdown[oid]["at_risk_count"] = int(owner_breakdown[oid]["at_risk_count"]) + 1

        total_value = sum(opp.amount or 0 for opp in opps)

        return {
            "total_deals": len(opps),
            "total_value": total_value,
            "by_stage": by_stage,
            "at_risk_deals": [opp.model_dump() for opp in at_risk],
            "owner_breakdown": owner_breakdown if manager_id else None,
        }

    except SalesforceClientError as e:
        return e.to_error_response()


@mcp.tool()
def get_deal_activity_gaps(
    owner_id: str | None = None,
    inactivity_threshold_days: int | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Identify open deals with activity gaps for Next Best Action prioritization.

    Returns deals sorted by urgency: overdue close dates first, then longest
    inactivity, then approaching close dates.

    Args:
        owner_id: Filter by opportunity owner User ID.
        inactivity_threshold_days: Override default inactivity threshold from risk_thresholds.yaml.
        limit: Maximum results (1-50, default 20).
    """
    limit = max(1, min(50, limit))

    try:
        sf = _get_sf_client()
        thresholds = _load_risk_thresholds()
        threshold_days = inactivity_threshold_days or thresholds.get("inactivity_days", 14)
        today = date.today()

        conditions = ["IsClosed = false"]
        if owner_id:
            conditions.append(f"OwnerId = '{owner_id}'")

        where_clause = " AND ".join(conditions)
        soql = (
            f"SELECT {OPP_FIELDS} FROM Opportunity "
            f"WHERE {where_clause} "
            f"ORDER BY CloseDate ASC LIMIT {limit * 2}"
        )
        records = sf.query(soql)
        opps = [_record_to_opportunity(r) for r in records]

        # Classify each deal
        overdue: list[dict[str, Any]] = []
        inactive: list[dict[str, Any]] = []
        approaching: list[dict[str, Any]] = []

        for opp in opps:
            _apply_risk_flags(opp, thresholds)
            days_since_activity = (
                (today - opp.last_activity_date).days if opp.last_activity_date else None
            )
            days_to_close = (opp.close_date - today).days

            entry = {
                **opp.model_dump(),
                "days_since_activity": days_since_activity,
                "days_to_close": days_to_close,
                "urgency": "",
                "recommended_action": "",
            }

            if days_to_close < 0:
                entry["urgency"] = "urgent"
                entry["recommended_action"] = (
                    f"Overdue by {abs(days_to_close)} days — re-engage decision maker "
                    f"or revise close date"
                )
                overdue.append(entry)
            elif days_since_activity is not None and days_since_activity > threshold_days:
                entry["urgency"] = "high"
                entry["recommended_action"] = (
                    f"No activity in {days_since_activity} days — schedule follow-up"
                )
                inactive.append(entry)
            elif days_since_activity is None:
                entry["urgency"] = "high"
                entry["recommended_action"] = "No recorded activity — initiate outreach"
                inactive.append(entry)
            elif 0 <= days_to_close <= 7:
                entry["urgency"] = "medium"
                entry["recommended_action"] = (
                    f"Closing in {days_to_close} days — verify next steps"
                )
                approaching.append(entry)

        # Sort inactive by longest gap first
        inactive.sort(
            key=lambda x: x.get("days_since_activity") or 9999, reverse=True
        )

        # Combine in priority order and trim to limit
        prioritized = (overdue + inactive + approaching)[:limit]

        return {
            "deals": prioritized,
            "total_count": len(prioritized),
            "summary": {
                "overdue": len(overdue),
                "inactive": len(inactive),
                "approaching": len(approaching),
            },
            "threshold_days": threshold_days,
        }

    except SalesforceClientError as e:
        return e.to_error_response()
