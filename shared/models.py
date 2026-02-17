"""Pydantic response models for MCP tool outputs.

All models correspond to Salesforce objects as defined in data-model.md.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class AccountSummary(BaseModel):
    """Summary of a Salesforce Account."""

    id: str = Field(description="Salesforce Account ID")
    name: str
    industry: str | None = None
    type: str | None = None
    annual_revenue: float | None = None
    billing_city: str | None = None
    billing_state: str | None = None
    owner_name: str | None = None
    description: str | None = None


class ContactSummary(BaseModel):
    """Summary of a Salesforce Contact."""

    id: str = Field(description="Salesforce Contact ID")
    name: str
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = Field(None, description="Opportunity contact role")


class OpportunitySummary(BaseModel):
    """Summary of a Salesforce Opportunity with risk indicators."""

    id: str = Field(description="Salesforce Opportunity ID")
    name: str
    amount: float | None = None
    stage: str
    close_date: date
    probability: float | None = None
    owner_name: str | None = None
    account_name: str | None = None
    last_activity_date: date | None = None
    risk_flags: list[str] = Field(default_factory=list, description="Risk indicators")


class PipelineSummary(BaseModel):
    """Aggregated pipeline summary with risk analysis."""

    total_deals: int
    total_value: float
    by_stage: dict[str, dict[str, int | float]] = Field(
        description="Stage -> {count, value}"
    )
    at_risk_deals: list[OpportunitySummary]
    owner_breakdown: dict[str, dict[str, str | int | float]] | None = None


class CaseSummary(BaseModel):
    """Summary of a Salesforce Case."""

    id: str = Field(description="Salesforce Case ID")
    case_number: str
    subject: str
    description: str | None = None
    status: str
    priority: str
    type: str | None = None
    created_date: datetime
    owner_name: str | None = None
    account_name: str | None = None
    recent_comments: list[str] = Field(default_factory=list)


class KnowledgeArticle(BaseModel):
    """Salesforce Knowledge Article."""

    id: str = Field(description="Knowledge Article Version ID")
    title: str
    summary: str | None = None
    url_name: str | None = None
    last_published: datetime | None = None
    article_type: str | None = None
    body: str | None = Field(
        None, description="Full article content (only from get_article_by_id)"
    )


class ActivitySummary(BaseModel):
    """Summary of a Salesforce Task or Event."""

    id: str
    type: str = Field(description="'Task' or 'Event'")
    subject: str
    date: date | None = None
    status: str | None = None
    owner_name: str | None = None


class LeadSummary(BaseModel):
    """Summary of a Salesforce Lead."""

    id: str = Field(description="Salesforce Lead ID")
    name: str
    company: str
    status: str
    lead_source: str | None = None
    email: str | None = None
    owner_name: str | None = None


class TeamMember(BaseModel):
    """Salesforce User (team member)."""

    id: str = Field(description="Salesforce User ID")
    name: str
    is_active: bool
    profile_name: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response from MCP tools."""

    code: str = Field(
        description="Error code: NOT_FOUND, PERMISSION_DENIED, RATE_LIMIT_WARNING, "
        "RATE_LIMIT_EXCEEDED, INVALID_INPUT, SF_API_ERROR, AUTH_ERROR, KNOWLEDGE_DISABLED"
    )
    message: str
    details: dict[str, str | int | float | bool | None] | None = None
