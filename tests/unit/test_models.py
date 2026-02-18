"""Unit tests for shared/models.py — all Pydantic response models."""

from datetime import date, datetime

from shared.models import (
    AccountSummary,
    ActivitySummary,
    CaseSummary,
    ContactSummary,
    ErrorResponse,
    KnowledgeArticle,
    LeadSummary,
    OpportunitySummary,
    PipelineSummary,
    TeamMember,
)


class TestAccountSummary:
    def test_minimal(self) -> None:
        account = AccountSummary(id="001ABC", name="Acme Corp")
        assert account.id == "001ABC"
        assert account.name == "Acme Corp"
        assert account.industry is None

    def test_full(self) -> None:
        account = AccountSummary(
            id="001ABC",
            name="Acme Corp",
            industry="Technology",
            type="Customer",
            annual_revenue=5_000_000.0,
            billing_city="San Francisco",
            billing_state="CA",
            owner_name="John Doe",
            description="A leading tech company",
        )
        assert account.annual_revenue == 5_000_000.0
        assert account.billing_state == "CA"

    def test_serialization(self) -> None:
        account = AccountSummary(id="001ABC", name="Acme Corp", industry="Tech")
        data = account.model_dump()
        assert data["id"] == "001ABC"
        assert data["industry"] == "Tech"


class TestContactSummary:
    def test_minimal(self) -> None:
        contact = ContactSummary(id="003ABC", name="Jane Smith")
        assert contact.name == "Jane Smith"
        assert contact.role is None

    def test_with_role(self) -> None:
        contact = ContactSummary(
            id="003ABC",
            name="Jane Smith",
            title="VP of Sales",
            email="jane@acme.com",
            phone="555-1234",
            role="Decision Maker",
        )
        assert contact.role == "Decision Maker"
        assert contact.email == "jane@acme.com"


class TestOpportunitySummary:
    def test_minimal(self) -> None:
        opp = OpportunitySummary(
            id="006ABC",
            name="Big Deal",
            stage="Prospecting",
            close_date=date(2026, 6, 30),
        )
        assert opp.stage == "Prospecting"
        assert opp.risk_flags == []

    def test_with_risk_flags(self) -> None:
        opp = OpportunitySummary(
            id="006ABC",
            name="Stalled Deal",
            stage="Negotiation/Review",
            close_date=date(2026, 1, 15),
            amount=50000.0,
            probability=20.0,
            risk_flags=["overdue", "low_probability", "no_activity_14d"],
        )
        assert len(opp.risk_flags) == 3
        assert "overdue" in opp.risk_flags

    def test_date_serialization(self) -> None:
        opp = OpportunitySummary(
            id="006ABC",
            name="Deal",
            stage="Closed Won",
            close_date=date(2026, 3, 15),
        )
        data = opp.model_dump()
        assert data["close_date"] == date(2026, 3, 15)


class TestPipelineSummary:
    def test_full(self) -> None:
        pipeline = PipelineSummary(
            total_deals=10,
            total_value=500_000.0,
            by_stage={
                "Prospecting": {"count": 3, "value": 100_000.0},
                "Negotiation/Review": {"count": 2, "value": 200_000.0},
            },
            at_risk_deals=[
                OpportunitySummary(
                    id="006ABC",
                    name="At Risk",
                    stage="Negotiation/Review",
                    close_date=date(2026, 1, 1),
                    risk_flags=["overdue"],
                )
            ],
            owner_breakdown={
                "user1": {"owner_name": "Alice", "deal_count": 5, "total_value": 250_000.0, "at_risk_count": 1}
            },
        )
        assert pipeline.total_deals == 10
        assert len(pipeline.at_risk_deals) == 1
        assert pipeline.owner_breakdown is not None


class TestCaseSummary:
    def test_minimal(self) -> None:
        case = CaseSummary(
            id="500ABC",
            case_number="00012345",
            subject="Login Issue",
            status="New",
            priority="High",
            created_date=datetime(2026, 2, 15, 10, 30, 0),
        )
        assert case.case_number == "00012345"
        assert case.recent_comments == []

    def test_with_comments(self) -> None:
        case = CaseSummary(
            id="500ABC",
            case_number="00012345",
            subject="Login Issue",
            status="Working",
            priority="High",
            created_date=datetime(2026, 2, 15),
            recent_comments=["Investigating", "Found root cause"],
        )
        assert len(case.recent_comments) == 2


class TestKnowledgeArticle:
    def test_search_result(self) -> None:
        article = KnowledgeArticle(id="kaXXX", title="How to Reset Password")
        assert article.body is None

    def test_full_article(self) -> None:
        article = KnowledgeArticle(
            id="kaXXX",
            title="How to Reset Password",
            summary="Steps to reset your password",
            url_name="how-to-reset-password",
            body="<p>Step 1: Go to settings...</p>",
            article_type="FAQ",
            last_published=datetime(2026, 1, 10),
        )
        assert article.body is not None
        assert article.article_type == "FAQ"


class TestActivitySummary:
    def test_task(self) -> None:
        activity = ActivitySummary(
            id="00TXXX",
            type="Task",
            subject="Follow up call",
            date=date(2026, 2, 20),
            status="Not Started",
        )
        assert activity.type == "Task"

    def test_event(self) -> None:
        activity = ActivitySummary(
            id="00UXXX",
            type="Event",
            subject="Client Meeting",
            date=date(2026, 2, 25),
        )
        assert activity.type == "Event"
        assert activity.status is None


class TestLeadSummary:
    def test_minimal(self) -> None:
        lead = LeadSummary(
            id="00QXXX",
            name="Bob Jones",
            company="NewCo",
            status="Open",
        )
        assert lead.company == "NewCo"

    def test_full(self) -> None:
        lead = LeadSummary(
            id="00QXXX",
            name="Bob Jones",
            company="NewCo",
            status="Working",
            lead_source="Web",
            email="bob@newco.com",
            owner_name="Alice",
        )
        assert lead.lead_source == "Web"


class TestTeamMember:
    def test_active(self) -> None:
        member = TeamMember(id="005XXX", name="Alice Johnson", is_active=True, profile_name="Sales User")
        assert member.is_active is True

    def test_inactive(self) -> None:
        member = TeamMember(id="005YYY", name="Former Employee", is_active=False)
        assert member.is_active is False
        assert member.profile_name is None


class TestErrorResponse:
    def test_basic(self) -> None:
        error = ErrorResponse(code="NOT_FOUND", message="Record not found")
        assert error.code == "NOT_FOUND"
        assert error.details is None

    def test_with_details(self) -> None:
        error = ErrorResponse(
            code="RATE_LIMIT_WARNING",
            message="Approaching limit",
            details={"usage_percent": 85.0, "calls_made": 850},
        )
        assert error.details is not None
        assert error.details["usage_percent"] == 85.0
