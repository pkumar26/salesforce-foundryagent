"""Unit tests for shared/salesforce_client.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from simple_salesforce import SalesforceError

from shared.salesforce_client import (
    ApiUsageTracker,
    SalesforceClient,
    SalesforceClientError,
    WriteBackConfirmationError,
)


class TestApiUsageTracker:
    def test_initial_state(self) -> None:
        tracker = ApiUsageTracker()
        assert tracker.calls_made == 0
        assert tracker.usage_percent == 0.0
        assert not tracker.is_warning
        assert not tracker.is_exceeded

    def test_record_call(self) -> None:
        tracker = ApiUsageTracker()
        tracker.record_call()
        assert tracker.calls_made == 1

    def test_warning_threshold(self) -> None:
        tracker = ApiUsageTracker(daily_limit=100, warning_threshold=0.80)
        for _ in range(80):
            tracker.record_call()
        assert tracker.is_warning
        assert not tracker.is_exceeded

    def test_exceeded(self) -> None:
        tracker = ApiUsageTracker(daily_limit=10)
        for _ in range(10):
            tracker.record_call()
        assert tracker.is_exceeded

    def test_get_status(self) -> None:
        tracker = ApiUsageTracker(daily_limit=100)
        tracker.record_call()
        status = tracker.get_status()
        assert status["calls_made"] == 1
        assert status["daily_limit"] == 100
        assert status["usage_percent"] == 1.0


class TestSalesforceClientError:
    def test_to_error_response(self) -> None:
        error = SalesforceClientError("NOT_FOUND", "Record not found", {"id": "001XXX"})
        response = error.to_error_response()
        assert response["error"]["code"] == "NOT_FOUND"
        assert response["error"]["message"] == "Record not found"
        assert response["error"]["details"]["id"] == "001XXX"

    def test_error_without_details(self) -> None:
        error = SalesforceClientError("AUTH_ERROR", "Invalid session")
        response = error.to_error_response()
        assert "details" not in response["error"]


class TestSalesforceClient:
    @patch("shared.salesforce_client.Salesforce")
    def test_init_success(self, mock_sf_class: MagicMock) -> None:
        SalesforceClient(
            instance_url="https://test.salesforce.com",
            access_token="test_token",
        )
        mock_sf_class.assert_called_once_with(
            instance_url="https://test.salesforce.com",
            session_id="test_token",
            version="62.0",
        )

    @patch("shared.salesforce_client.Salesforce")
    def test_init_auth_error(self, mock_sf_class: MagicMock) -> None:
        mock_sf_class.side_effect = SalesforceError(
            "https://test.salesforce.com", 401, "auth", b"Invalid session"
        )
        with pytest.raises(SalesforceClientError) as exc_info:
            SalesforceClient(
                instance_url="https://test.salesforce.com",
                access_token="bad_token",
            )
        assert exc_info.value.code == "AUTH_ERROR"

    @patch("shared.salesforce_client.Salesforce")
    def test_query_success(self, mock_sf_class: MagicMock) -> None:
        mock_sf = MagicMock()
        mock_sf.query.return_value = {
            "records": [
                {"attributes": {"type": "Account"}, "Id": "001XXX", "Name": "Acme"}
            ]
        }
        mock_sf_class.return_value = mock_sf

        client = SalesforceClient("https://test.salesforce.com", "token")
        results = client.query("SELECT Id, Name FROM Account LIMIT 1")

        assert len(results) == 1
        assert results[0]["Id"] == "001XXX"
        assert "attributes" not in results[0]
        assert client.usage.calls_made == 1

    @patch("shared.salesforce_client.Salesforce")
    def test_query_auth_error(self, mock_sf_class: MagicMock) -> None:
        mock_sf = MagicMock()
        mock_sf.query.side_effect = SalesforceError(
            "https://test.salesforce.com", 401, "query", b"INVALID_SESSION_ID"
        )
        mock_sf_class.return_value = mock_sf

        client = SalesforceClient("https://test.salesforce.com", "token")
        with pytest.raises(SalesforceClientError) as exc_info:
            client.query("SELECT Id FROM Account")
        assert exc_info.value.code == "AUTH_ERROR"

    @patch("shared.salesforce_client.Salesforce")
    def test_query_rate_limit_exceeded(self, mock_sf_class: MagicMock) -> None:
        mock_sf = MagicMock()
        mock_sf_class.return_value = mock_sf

        client = SalesforceClient("https://test.salesforce.com", "token")
        client._usage = ApiUsageTracker(daily_limit=0)

        with pytest.raises(SalesforceClientError) as exc_info:
            client.query("SELECT Id FROM Account")
        assert exc_info.value.code == "RATE_LIMIT_EXCEEDED"

    @patch("shared.salesforce_client.Salesforce")
    def test_create_record_requires_confirmation(self, mock_sf_class: MagicMock) -> None:
        mock_sf_class.return_value = MagicMock()
        client = SalesforceClient("https://test.salesforce.com", "token")

        with pytest.raises(WriteBackConfirmationError):
            client.create_record("Case", {"Subject": "Test"})

    @patch("shared.salesforce_client.Salesforce")
    def test_create_record_confirmed(self, mock_sf_class: MagicMock) -> None:
        mock_sf = MagicMock()
        mock_sf.Case.create.return_value = {"id": "500XXX", "success": True}
        mock_sf_class.return_value = mock_sf

        client = SalesforceClient("https://test.salesforce.com", "token")
        result = client.create_record("Case", {"Subject": "Test"}, confirmed=True)

        assert result["id"] == "500XXX"
        assert result["success"] is True

    @patch("shared.salesforce_client.Salesforce")
    def test_update_record_requires_confirmation(self, mock_sf_class: MagicMock) -> None:
        mock_sf_class.return_value = MagicMock()
        client = SalesforceClient("https://test.salesforce.com", "token")

        with pytest.raises(WriteBackConfirmationError):
            client.update_record("Case", "500XXX", {"Status": "Working"})

    @patch("shared.salesforce_client.Salesforce")
    def test_update_record_confirmed(self, mock_sf_class: MagicMock) -> None:
        mock_sf = MagicMock()
        mock_sf.Case.update.return_value = None
        mock_sf_class.return_value = mock_sf

        client = SalesforceClient("https://test.salesforce.com", "token")
        result = client.update_record("Case", "500XXX", {"Status": "Working"}, confirmed=True)

        assert result is True

    @patch("shared.salesforce_client.Salesforce")
    def test_search(self, mock_sf_class: MagicMock) -> None:
        mock_sf = MagicMock()
        mock_sf.search.return_value = {
            "searchRecords": [
                {"attributes": {"type": "KnowledgeArticleVersion"}, "Id": "kaXXX", "Title": "Article"}
            ]
        }
        mock_sf_class.return_value = mock_sf

        client = SalesforceClient("https://test.salesforce.com", "token")
        results = client.search("FIND {test} RETURNING KnowledgeArticleVersion(Id, Title)")

        assert len(results) == 1
        assert "attributes" not in results[0]
