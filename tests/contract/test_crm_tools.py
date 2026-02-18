"""Contract tests for Salesforce CRM MCP tools.

Tests validate tool output schemas against mock Salesforce responses.
These are synchronous tests using unittest.mock to substitute the SalesforceClient.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# --- Fixtures ---

@pytest.fixture
def mock_sf_client():
    """Create a mock SalesforceClient."""
    client = MagicMock()
    client.usage = MagicMock()
    client.usage.is_warning = False
    client.usage.is_exceeded = False
    return client


ACCOUNT_RECORD = {
    "Id": "001000000000001",
    "Name": "Acme Corp",
    "Industry": "Technology",
    "Type": "Customer",
    "AnnualRevenue": 5000000.0,
    "BillingCity": "San Francisco",
    "BillingState": "CA",
    "Owner": {"Name": "Jane Smith"},
    "Description": "Enterprise technology company",
}

CONTACT_RECORD = {
    "Id": "003000000000001",
    "Name": "John Doe",
    "Title": "VP Sales",
    "Email": "john@acme.com",
    "Phone": "555-0100",
}

OPPORTUNITY_RECORD = {
    "Id": "006000000000001",
    "Name": "Acme - Enterprise License",
    "Amount": 250000.0,
    "StageName": "Proposal/Price Quote",
    "CloseDate": "2025-03-15",
    "Probability": 60.0,
    "Owner": {"Name": "Jane Smith"},
    "Account": {"Name": "Acme Corp"},
    "LastActivityDate": "2025-01-15",
}

TASK_RECORD = {
    "Id": "00T000000000001",
    "Subject": "Follow up call",
    "ActivityDate": "2025-02-01",
    "Status": "Completed",
    "Owner": {"Name": "Jane Smith"},
}

EVENT_RECORD = {
    "Id": "00U000000000001",
    "Subject": "Quarterly Review",
    "ActivityDate": "2025-02-10",
    "Owner": {"Name": "Jane Smith"},
}

CASE_RECORD = {
    "Id": "500000000000001",
    "CaseNumber": "00012345",
    "Subject": "Login issues",
    "Description": "Cannot log in to portal",
    "Status": "New",
    "Priority": "High",
    "Type": "Problem",
    "CreatedDate": "2025-02-01T10:00:00.000+0000",
    "Owner": {"Name": "Agent Smith"},
    "Account": {"Name": "Acme Corp"},
}

LEAD_RECORD = {
    "Id": "00Q000000000001",
    "Name": "Alice Johnson",
    "Company": "Widgets Inc",
    "Status": "Working",
    "LeadSource": "Web",
    "Email": "alice@widgets.com",
    "Owner": {"Name": "Jane Smith"},
}

USER_RECORD = {
    "Id": "005000000000001",
    "Name": "Bob Rep",
    "IsActive": True,
    "Profile": {"Name": "Sales User"},
}


# --- Account Tools ---

class TestGetAccount:
    """Contract tests for get_account tool."""

    @patch("mcp_servers.salesforce_crm.tools.accounts._get_sf_client")
    def test_get_account_by_id(self, mock_get_client, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.return_value = [ACCOUNT_RECORD]

        from mcp_servers.salesforce_crm.tools.accounts import get_account

        result = get_account(account_id="001000000000001")

        assert result["match_count"] == 1
        assert result["account"]["id"] == "001000000000001"
        assert result["account"]["name"] == "Acme Corp"
        assert result["account"]["industry"] == "Technology"

    @patch("mcp_servers.salesforce_crm.tools.accounts._get_sf_client")
    def test_get_account_by_name_single(self, mock_get_client, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.return_value = [ACCOUNT_RECORD]

        from mcp_servers.salesforce_crm.tools.accounts import get_account

        result = get_account(account_name="Acme")

        assert result["match_count"] == 1
        assert result["account"]["name"] == "Acme Corp"

    @patch("mcp_servers.salesforce_crm.tools.accounts._get_sf_client")
    def test_get_account_by_name_multiple(self, mock_get_client, mock_sf_client):
        record2 = {**ACCOUNT_RECORD, "Id": "001000000000002", "Name": "Acme Labs"}
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.return_value = [ACCOUNT_RECORD, record2]

        from mcp_servers.salesforce_crm.tools.accounts import get_account

        result = get_account(account_name="Acme")

        assert result["match_count"] == 2
        assert result["account"] is None
        assert len(result["matches"]) == 2

    @patch("mcp_servers.salesforce_crm.tools.accounts._get_sf_client")
    def test_get_account_not_found(self, mock_get_client, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.return_value = []

        from mcp_servers.salesforce_crm.tools.accounts import get_account

        result = get_account(account_id="001000000000999")

        assert "code" in result or "error" in result or result.get("code") == "NOT_FOUND"

    def test_get_account_no_input(self):
        from mcp_servers.salesforce_crm.tools.accounts import get_account

        result = get_account()
        assert result["code"] == "INVALID_INPUT"


class TestSearchAccounts:
    """Contract tests for search_accounts tool."""

    @patch("mcp_servers.salesforce_crm.tools.accounts._get_sf_client")
    def test_search_accounts_basic(self, mock_get_client, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.return_value = [ACCOUNT_RECORD]

        from mcp_servers.salesforce_crm.tools.accounts import search_accounts

        result = search_accounts(query="Acme")

        assert "accounts" in result
        assert result["total_count"] == 1
        assert result["has_more"] is False
        assert result["accounts"][0]["name"] == "Acme Corp"

    @patch("mcp_servers.salesforce_crm.tools.accounts._get_sf_client")
    def test_search_accounts_with_filters(self, mock_get_client, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.return_value = [ACCOUNT_RECORD]

        from mcp_servers.salesforce_crm.tools.accounts import search_accounts

        result = search_accounts(query="Acme", industry="Technology")

        assert result["total_count"] == 1
        # Verify the query included industry filter
        call_args = mock_sf_client.query.call_args[0][0]
        assert "Industry = 'Technology'" in call_args


# --- Contact Tools ---

class TestGetContactsForAccount:
    """Contract tests for get_contacts_for_account tool."""

    @patch("mcp_servers.salesforce_crm.tools.contacts._get_sf_client")
    def test_get_contacts(self, mock_get_client, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.side_effect = [
            [CONTACT_RECORD],  # Contact query
            [{"ContactId": "003000000000001", "Role": "Decision Maker"}],  # Roles query
        ]

        from mcp_servers.salesforce_crm.tools.contacts import get_contacts_for_account

        result = get_contacts_for_account(account_id="001000000000001")

        assert "contacts" in result
        assert result["total_count"] == 1
        assert result["contacts"][0]["name"] == "John Doe"
        assert result["contacts"][0]["role"] == "Decision Maker"


# --- Opportunity Tools ---

class TestGetOpportunities:
    """Contract tests for get_opportunities tool."""

    @patch("mcp_servers.salesforce_crm.tools.opportunities._get_sf_client")
    def test_get_opportunities_basic(self, mock_get_client, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.return_value = [OPPORTUNITY_RECORD]

        from mcp_servers.salesforce_crm.tools.opportunities import get_opportunities

        result = get_opportunities()

        assert "opportunities" in result
        assert result["total_count"] == 1
        assert result["total_value"] == 250000.0
        assert result["opportunities"][0]["name"] == "Acme - Enterprise License"

    @patch("mcp_servers.salesforce_crm.tools.opportunities._get_sf_client")
    def test_get_opportunities_with_filters(self, mock_get_client, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.return_value = [OPPORTUNITY_RECORD]

        from mcp_servers.salesforce_crm.tools.opportunities import get_opportunities

        result = get_opportunities(
            owner_id="005000000000001",
            stage="Proposal/Price Quote",
        )

        assert result["total_count"] == 1
        call_args = mock_sf_client.query.call_args[0][0]
        assert "OwnerId" in call_args
        assert "StageName" in call_args


class TestGetPipelineSummary:
    """Contract tests for get_pipeline_summary tool."""

    @patch("mcp_servers.salesforce_crm.tools.opportunities._load_risk_thresholds")
    @patch("mcp_servers.salesforce_crm.tools.opportunities._get_sf_client")
    def test_pipeline_summary_single_owner(self, mock_get_client, mock_thresholds, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.return_value = [OPPORTUNITY_RECORD]
        mock_thresholds.return_value = {
            "stage_stagnation_days": 30,
            "inactivity_days": 14,
            "low_probability_threshold": 30,
            "overdue_close_date": {"enabled": True},
            "late_stages": ["Negotiation/Review"],
            "minimum_amount_for_risk": 10000,
        }

        from mcp_servers.salesforce_crm.tools.opportunities import get_pipeline_summary

        result = get_pipeline_summary(owner_id="005000000000001")

        assert result["total_deals"] == 1
        assert result["total_value"] == 250000.0
        assert "Proposal/Price Quote" in result["by_stage"]
        assert isinstance(result["at_risk_deals"], list)

    @patch("mcp_servers.salesforce_crm.tools.opportunities._load_risk_thresholds")
    @patch("mcp_servers.salesforce_crm.tools.opportunities._get_sf_client")
    def test_pipeline_summary_manager(self, mock_get_client, mock_thresholds, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.side_effect = [
            [{"Id": "005000000000001"}],  # Team members
            [OPPORTUNITY_RECORD],  # Opportunities
        ]
        mock_thresholds.return_value = {
            "stage_stagnation_days": 30,
            "inactivity_days": 14,
            "low_probability_threshold": 30,
            "overdue_close_date": {"enabled": True},
            "late_stages": [],
            "minimum_amount_for_risk": 10000,
        }

        from mcp_servers.salesforce_crm.tools.opportunities import get_pipeline_summary

        result = get_pipeline_summary(manager_id="005000000000099")

        assert result["total_deals"] == 1
        assert result["owner_breakdown"] is not None


# --- Activity Tools ---

class TestGetRecentActivities:
    """Contract tests for get_recent_activities tool."""

    @patch("mcp_servers.salesforce_crm.tools.activities._get_sf_client")
    def test_get_recent_activities(self, mock_get_client, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.side_effect = [
            [TASK_RECORD],  # Tasks
            [EVENT_RECORD],  # Events
        ]

        from mcp_servers.salesforce_crm.tools.activities import get_recent_activities

        result = get_recent_activities(related_to_id="001000000000001")

        assert "activities" in result
        assert result["total_count"] == 2
        types = {a["type"] for a in result["activities"]}
        assert "Task" in types
        assert "Event" in types


class TestCreateTask:
    """Contract tests for create_task tool."""

    @patch("mcp_servers.salesforce_crm.tools.activities._get_sf_client")
    def test_create_task_requires_confirmation(self, mock_get_client, mock_sf_client):
        from shared.salesforce_client import WriteBackConfirmationError

        mock_get_client.return_value = mock_sf_client
        mock_sf_client.create_record.side_effect = WriteBackConfirmationError(
            "create_task", {"object": "Task", "data": {"Subject": "Follow up"}}
        )

        from mcp_servers.salesforce_crm.tools.activities import create_task

        result = create_task(subject="Follow up")

        assert result["success"] is False
        assert "confirm" in result["message"].lower()

    @patch("mcp_servers.salesforce_crm.tools.activities._get_sf_client")
    def test_create_task_confirmed(self, mock_get_client, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.create_record.return_value = {"id": "00T000000000002", "success": True}

        from mcp_servers.salesforce_crm.tools.activities import create_task

        result = create_task(subject="Follow up", confirmed=True)

        assert result["success"] is True
        assert result["task_id"] == "00T000000000002"


# --- Output Schema Validation ---

class TestOutputSchemas:
    """Verify output shapes match contract definitions."""

    @patch("mcp_servers.salesforce_crm.tools.accounts._get_sf_client")
    def test_get_account_output_shape(self, mock_get_client, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.return_value = [ACCOUNT_RECORD]

        from mcp_servers.salesforce_crm.tools.accounts import get_account

        result = get_account(account_id="001000000000001")

        # Verify required output keys
        assert "account" in result
        assert "match_count" in result
        assert "matches" in result

        # Verify account shape
        acct = result["account"]
        assert "id" in acct
        assert "name" in acct

    @patch("mcp_servers.salesforce_crm.tools.accounts._get_sf_client")
    def test_search_accounts_output_shape(self, mock_get_client, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.return_value = [ACCOUNT_RECORD]

        from mcp_servers.salesforce_crm.tools.accounts import search_accounts

        result = search_accounts(query="Acme")

        assert "accounts" in result
        assert "total_count" in result
        assert "has_more" in result
        assert isinstance(result["accounts"], list)

    @patch("mcp_servers.salesforce_crm.tools.contacts._get_sf_client")
    def test_contacts_output_shape(self, mock_get_client, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.side_effect = [[CONTACT_RECORD], []]

        from mcp_servers.salesforce_crm.tools.contacts import get_contacts_for_account

        result = get_contacts_for_account(account_id="001000000000001")

        assert "contacts" in result
        assert "total_count" in result
        assert isinstance(result["contacts"], list)

    @patch("mcp_servers.salesforce_crm.tools.opportunities._get_sf_client")
    def test_opportunities_output_shape(self, mock_get_client, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.return_value = [OPPORTUNITY_RECORD]

        from mcp_servers.salesforce_crm.tools.opportunities import get_opportunities

        result = get_opportunities()

        assert "opportunities" in result
        assert "total_count" in result
        assert "total_value" in result

    @patch("mcp_servers.salesforce_crm.tools.activities._get_sf_client")
    def test_activities_output_shape(self, mock_get_client, mock_sf_client):
        mock_get_client.return_value = mock_sf_client
        mock_sf_client.query.side_effect = [[TASK_RECORD], [EVENT_RECORD]]

        from mcp_servers.salesforce_crm.tools.activities import get_recent_activities

        result = get_recent_activities(related_to_id="001000000000001")

        assert "activities" in result
        assert "total_count" in result
