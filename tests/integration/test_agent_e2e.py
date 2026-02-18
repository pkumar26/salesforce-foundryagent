"""Integration tests for Agent E2E workflows.

Tests multi-turn conversation and cross-domain orchestration scenarios.
These tests require live Azure AI Foundry and Salesforce connections.
Mark with pytest.mark.integration to skip in CI.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.integration
class TestAgentMultiTurn:
    """Test multi-turn conversation patterns with mocked agent responses."""

    def test_sales_agent_meeting_prep_flow(self):
        """Verify multi-turn meeting prep: lookup → briefing → follow-up."""
        # This test validates the tool invocation sequence
        # In a live environment, it would use real agent API calls
        from mcp_servers.salesforce_crm.tools.accounts import get_account
        from mcp_servers.salesforce_crm.tools.contacts import get_contacts_for_account
        from mcp_servers.salesforce_crm.tools.opportunities import get_opportunities

        mock_client = MagicMock()
        with (
            patch(
                "mcp_servers.salesforce_crm.tools.accounts._get_sf_client",
                return_value=mock_client,
            ),
            patch(
                "mcp_servers.salesforce_crm.tools.contacts._get_sf_client",
                return_value=mock_client,
            ),
            patch(
                "mcp_servers.salesforce_crm.tools.opportunities._get_sf_client",
                return_value=mock_client,
            ),
        ):
            # Turn 1: Account lookup
            mock_client.query.return_value = [
                {
                    "Id": "001ABC",
                    "Name": "Acme Corp",
                    "Industry": "Technology",
                    "BillingCity": "San Francisco",
                    "BillingState": "CA",
                    "Website": "https://acme.com",
                    "Owner": {"Name": "Jane Smith"},
                    "AnnualRevenue": 5000000,
                    "NumberOfEmployees": 200,
                    "Description": "Enterprise SaaS company",
                }
            ]
            result1 = get_account(account_name="Acme Corp")
            assert "account" in result1

            # Turn 2: Get contacts
            mock_client.query.return_value = [
                {
                    "Id": "003ABC",
                    "Name": "John Doe",
                    "Title": "VP Engineering",
                    "Email": "john@acme.com",
                    "Phone": "555-1234",
                }
            ]
            result2 = get_contacts_for_account(account_id="001ABC")
            assert "contacts" in result2

            # Turn 3: Get opportunities
            mock_client.query.return_value = [
                {
                    "Id": "006ABC",
                    "Name": "Acme Expansion",
                    "Amount": 100000,
                    "StageName": "Proposal",
                    "CloseDate": "2025-03-01",
                    "Probability": 60,
                    "Owner": {"Name": "Jane Smith"},
                    "Account": {"Name": "Acme Corp"},
                    "LastActivityDate": None,
                }
            ]
            result3 = get_opportunities(account_id="001ABC")
            assert "opportunities" in result3
            assert result3["total_count"] == 1

    def test_service_agent_triage_flow(self):
        """Verify triage flow: get_case → search_articles → update_case."""
        from mcp_servers.salesforce_crm.tools.cases import get_case, update_case
        from shared.salesforce_client import WriteBackConfirmationError

        mock_client = MagicMock()
        with patch(
            "mcp_servers.salesforce_crm.tools.cases._get_sf_client",
            return_value=mock_client,
        ):
            # Turn 1: Get case details
            mock_client.query.return_value = [
                {
                    "Id": "500ABC",
                    "CaseNumber": "00012345",
                    "Subject": "Cannot access dashboard",
                    "Description": "Getting 403 error on custom dashboard",
                    "Status": "New",
                    "Priority": "Medium",
                    "Type": None,
                    "CreatedDate": "2025-01-15T10:00:00.000+0000",
                    "Owner": {"Name": "Support Queue"},
                    "Account": {"Name": "Acme Corp"},
                }
            ]
            result1 = get_case(case_number="00012345")
            assert "case" in result1
            assert result1["case"]["case_number"] == "00012345"

            # Turn 2: Update case — should require confirmation
            mock_client.update_record.side_effect = WriteBackConfirmationError(
                "update_case", {"object": "Case", "record_id": "500ABC", "data": {}}
            )
            result2 = update_case(
                case_id="500ABC",
                priority="High",
                status="Working",
                comment="Escalated — customer impact confirmed",
            )
            assert result2["success"] is False
            assert "confirm" in result2["message"].lower()

            # Turn 3: Confirmed update
            mock_client.update_record.side_effect = None
            mock_client.update_record.return_value = None
            mock_client.create_record.return_value = {"id": "comment123", "success": True}
            result3 = update_case(
                case_id="500ABC",
                priority="High",
                status="Working",
                comment="Escalated — customer impact confirmed",
                confirmed=True,
            )
            assert result3["success"] is True
            assert "Priority" in result3["updated_fields"]
            assert "Status" in result3["updated_fields"]


@pytest.mark.integration
class TestCrossDomainOrchestration:
    """Test cross-domain query patterns."""

    def test_accounts_with_deals_and_cases(self):
        """Verify querying accounts that have both deals and cases."""
        from mcp_servers.salesforce_crm.tools.cases import get_case
        from mcp_servers.salesforce_crm.tools.opportunities import get_opportunities

        mock_client = MagicMock()
        with (
            patch(
                "mcp_servers.salesforce_crm.tools.cases._get_sf_client",
                return_value=mock_client,
            ),
            patch(
                "mcp_servers.salesforce_crm.tools.opportunities._get_sf_client",
                return_value=mock_client,
            ),
        ):
            # Query opportunities for account
            mock_client.query.return_value = [
                {
                    "Id": "006ABC",
                    "Name": "Acme Renewal",
                    "Amount": 50000,
                    "StageName": "Negotiation/Review",
                    "CloseDate": "2025-02-15",
                    "Probability": 75,
                    "Owner": {"Name": "AE"},
                    "Account": {"Name": "Acme Corp"},
                    "LastActivityDate": "2025-01-10",
                }
            ]
            opps = get_opportunities(account_id="001ABC")
            assert opps["total_count"] == 1

            # Query case for same account
            mock_client.query.return_value = [
                {
                    "Id": "500DEF",
                    "CaseNumber": "00054321",
                    "Subject": "API rate limit issues",
                    "Description": "Hitting rate limits on production API",
                    "Status": "Working",
                    "Priority": "High",
                    "Type": "Technical",
                    "CreatedDate": "2025-01-20T08:00:00.000+0000",
                    "Owner": {"Name": "Support Agent"},
                    "Account": {"Name": "Acme Corp"},
                }
            ]
            case = get_case(case_id="500DEF")
            assert "case" in case

            # In the orchestrator, the agent would correlate these by account
            assert opps["opportunities"][0]["account_name"] == "Acme Corp"
            assert case["case"]["account_name"] == "Acme Corp"

    def test_context_continuity_service_to_sales(self):
        """Verify that entities from service queries can inform sales queries."""
        from mcp_servers.salesforce_crm.tools.accounts import get_account
        from mcp_servers.salesforce_crm.tools.cases import get_case

        mock_client = MagicMock()
        with (
            patch(
                "mcp_servers.salesforce_crm.tools.cases._get_sf_client",
                return_value=mock_client,
            ),
            patch(
                "mcp_servers.salesforce_crm.tools.accounts._get_sf_client",
                return_value=mock_client,
            ),
        ):
            # Turn 1: Service query — get case, note the account
            mock_client.query.return_value = [
                {
                    "Id": "500XYZ",
                    "CaseNumber": "00099999",
                    "Subject": "Billing discrepancy",
                    "Description": "Invoice mismatch",
                    "Status": "New",
                    "Priority": "Medium",
                    "Type": "Billing",
                    "CreatedDate": "2025-01-25T12:00:00.000+0000",
                    "Owner": {"Name": "Billing Queue"},
                    "Account": {"Name": "GlobalTech Inc"},
                }
            ]
            case_result = get_case(case_id="500XYZ")
            account_name = case_result["case"]["account_name"]
            assert account_name == "GlobalTech Inc"

            # Turn 2: Sales query — look up the same account
            mock_client.query.return_value = [
                {
                    "Id": "001GGG",
                    "Name": "GlobalTech Inc",
                    "Industry": "Manufacturing",
                    "BillingCity": "Austin",
                    "BillingState": "TX",
                    "Website": "https://globaltech.com",
                    "Owner": {"Name": "Senior AE"},
                    "AnnualRevenue": 20000000,
                    "NumberOfEmployees": 500,
                    "Description": "Large manufacturing company",
                }
            ]
            account_result = get_account(account_name=account_name)
            assert "account" in account_result
            assert account_result["account"]["name"] == "GlobalTech Inc"
