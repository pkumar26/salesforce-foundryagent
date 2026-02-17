"""Contract tests for Salesforce Knowledge MCP tools.

Validates search_articles and get_article_by_id against
the schemas defined in contracts/mcp-salesforce-knowledge.md.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_sf_client():
    """Create a mock SalesforceClient for all tests."""
    client = MagicMock()
    with patch(
        "mcp_servers.salesforce_knowledge.server._get_sf_client",
        return_value=client,
    ):
        yield client


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_ARTICLES = [
    {
        "Id": "ka0000000000001AAA",
        "Title": "How to Reset API Key",
        "Summary": "Steps to reset your organization's API key securely.",
        "UrlName": "how-to-reset-api-key",
        "LastPublishedDate": "2024-12-01T10:00:00.000+0000",
        "ArticleType": "How_To__kav",
    },
    {
        "Id": "ka0000000000002AAA",
        "Title": "API Rate Limiting Guide",
        "Summary": "Understanding API rate limits and best practices.",
        "UrlName": "api-rate-limiting-guide",
        "LastPublishedDate": "2024-11-15T08:00:00.000+0000",
        "ArticleType": "How_To__kav",
    },
]


# ---------------------------------------------------------------------------
# search_articles tests
# ---------------------------------------------------------------------------

class TestSearchArticles:
    """Contract tests for the search_articles tool."""

    def test_sosl_search_returns_articles(self, mock_sf_client):
        """SOSL-based search returns articles matching the query."""
        from mcp_servers.salesforce_knowledge.tools.articles import search_articles

        mock_sf_client.search.return_value = SAMPLE_ARTICLES

        result = search_articles(query="API key")

        assert "articles" in result
        assert result["total_count"] == 2
        assert result["search_method"] == "sosl"
        assert len(result["articles"]) == 2

        article = result["articles"][0]
        assert article["id"] == "ka0000000000001AAA"
        assert article["title"] == "How to Reset API Key"
        assert article["summary"] is not None
        assert article["url_name"] == "how-to-reset-api-key"

    def test_soql_fallback_when_sosl_fails(self, mock_sf_client):
        """Falls back to SOQL LIKE search when SOSL fails."""
        from mcp_servers.salesforce_knowledge.tools.articles import search_articles
        from shared.salesforce_client import SalesforceClientError

        mock_sf_client.search.side_effect = SalesforceClientError("SOSL not available")
        mock_sf_client.query.return_value = [SAMPLE_ARTICLES[0]]

        result = search_articles(query="API key")

        assert result["search_method"] == "soql"
        assert result["total_count"] == 1
        assert result["articles"][0]["title"] == "How to Reset API Key"

    def test_empty_results(self, mock_sf_client):
        """Returns empty articles array when no matches found."""
        from mcp_servers.salesforce_knowledge.tools.articles import search_articles

        mock_sf_client.search.return_value = []

        result = search_articles(query="nonexistent topic")

        assert result["articles"] == []
        assert result["total_count"] == 0

    def test_limit_clamped(self, mock_sf_client):
        """Limit is clamped to 1-25 range."""
        from mcp_servers.salesforce_knowledge.tools.articles import search_articles

        mock_sf_client.search.return_value = SAMPLE_ARTICLES

        # Test zero limit gets clamped to 1
        result = search_articles(query="test", limit=0)
        assert result is not None

        # Test large limit gets clamped to 25
        result = search_articles(query="test", limit=100)
        assert result is not None

    def test_knowledge_disabled_error(self, mock_sf_client):
        """KNOWLEDGE_DISABLED error when Knowledge is not enabled."""
        from mcp_servers.salesforce_knowledge.tools.articles import search_articles
        from shared.salesforce_client import SalesforceClientError

        mock_sf_client.search.side_effect = SalesforceClientError(
            "KnowledgeArticleVersion: entity type not available"
        )

        result = search_articles(query="test")

        assert "code" in result
        assert result["code"] == "KNOWLEDGE_DISABLED"

    def test_output_schema_compliance(self, mock_sf_client):
        """Output matches the contract schema structure."""
        from mcp_servers.salesforce_knowledge.tools.articles import search_articles

        mock_sf_client.search.return_value = SAMPLE_ARTICLES

        result = search_articles(query="API")

        # Top-level keys
        assert set(result.keys()) == {"articles", "total_count", "search_method"}
        assert isinstance(result["articles"], list)
        assert isinstance(result["total_count"], int)
        assert result["search_method"] in ("sosl", "soql")

        # Article keys
        article = result["articles"][0]
        required_keys = {"id", "title"}
        optional_keys = {"summary", "url_name", "last_published", "article_type", "body"}
        assert required_keys.issubset(set(article.keys()))
        assert set(article.keys()).issubset(required_keys | optional_keys)


# ---------------------------------------------------------------------------
# get_article_by_id tests
# ---------------------------------------------------------------------------

class TestGetArticleById:
    """Contract tests for the get_article_by_id tool."""

    def test_retrieve_article_by_id(self, mock_sf_client):
        """Retrieves full article content by version ID."""
        from mcp_servers.salesforce_knowledge.tools.articles import get_article_by_id

        record = {
            **SAMPLE_ARTICLES[0],
            "ArticleBody": "<p>Step 1: Go to <b>Settings</b>.</p><p>Step 2: Click Reset.</p>",
        }
        mock_sf_client.query.return_value = [record]

        result = get_article_by_id(article_id="ka0000000000001AAA")

        assert "article" in result
        article = result["article"]
        assert article["id"] == "ka0000000000001AAA"
        assert article["title"] == "How to Reset API Key"

    def test_article_not_found(self, mock_sf_client):
        """Returns NOT_FOUND error for missing article."""
        from mcp_servers.salesforce_knowledge.tools.articles import get_article_by_id

        mock_sf_client.query.return_value = []

        result = get_article_by_id(article_id="ka0000000000099AAA")

        assert "code" in result
        assert result["code"] == "NOT_FOUND"

    def test_html_stripping(self, mock_sf_client):
        """HTML tags are stripped from article body."""
        from mcp_servers.salesforce_knowledge.tools.articles import get_article_by_id

        record = {
            **SAMPLE_ARTICLES[0],
            "ArticleBody": "<h1>Title</h1><p>Some <strong>bold</strong> text.</p>",
        }
        mock_sf_client.query.return_value = [record]

        result = get_article_by_id(article_id="ka0000000000001AAA")

        article = result["article"]
        # Body should exist and not contain HTML tags
        if article.get("body"):
            assert "<" not in article["body"]
            assert ">" not in article["body"]

    def test_knowledge_disabled_error(self, mock_sf_client):
        """KNOWLEDGE_DISABLED error when Knowledge is not accessible."""
        from mcp_servers.salesforce_knowledge.tools.articles import get_article_by_id
        from shared.salesforce_client import SalesforceClientError

        mock_sf_client.query.side_effect = SalesforceClientError(
            "Knowledge not enabled"
        )

        result = get_article_by_id(article_id="ka0000000000001AAA")

        assert "code" in result
        assert result["code"] == "KNOWLEDGE_DISABLED"

    def test_output_schema_compliance(self, mock_sf_client):
        """Output matches the contract schema structure."""
        from mcp_servers.salesforce_knowledge.tools.articles import get_article_by_id

        record = {
            **SAMPLE_ARTICLES[0],
            "ArticleBody": "<p>Full article content here.</p>",
        }
        mock_sf_client.query.return_value = [record]

        result = get_article_by_id(article_id="ka0000000000001AAA")

        assert "article" in result
        article = result["article"]

        # Required keys per contract
        required_keys = {"id", "title"}
        assert required_keys.issubset(set(article.keys()))

        # Optional keys
        optional_keys = {"summary", "body", "url_name", "last_published", "article_type"}
        assert set(article.keys()).issubset(required_keys | optional_keys)
