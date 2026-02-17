"""Knowledge Article tools for the Salesforce Knowledge MCP Server.

Implements: search_articles, get_article_by_id
Contract: contracts/mcp-salesforce-knowledge.md
"""

from __future__ import annotations

import logging
import re
from typing import Any

from mcp_servers.salesforce_knowledge.server import _get_sf_client, mcp
from shared.models import ErrorResponse, KnowledgeArticle
from shared.salesforce_client import SalesforceClientError

logger = logging.getLogger(__name__)


ARTICLE_FIELDS = (
    "Id, Title, Summary, UrlName, LastPublishedDate, ArticleType"
)

ARTICLE_BODY_FIELDS = (
    "Id, Title, Summary, UrlName, LastPublishedDate, ArticleType"
)


def _strip_html(html: str) -> str:
    """Strip HTML tags and return plain text."""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _record_to_article(record: dict[str, Any], include_body: bool = False) -> KnowledgeArticle:
    """Transform a Salesforce KnowledgeArticleVersion record to KnowledgeArticle."""
    return KnowledgeArticle(
        id=record.get("Id", ""),
        title=record.get("Title", ""),
        summary=record.get("Summary"),
        url_name=record.get("UrlName"),
        last_published=record.get("LastPublishedDate"),
        article_type=record.get("ArticleType"),
        body=_strip_html(record.get("ArticleBody", "")) if include_body else None,
    )


@mcp.tool()
def search_articles(
    query: str,
    language: str = "en_US",
    limit: int = 10,
) -> dict[str, Any]:
    """Search Salesforce Knowledge Articles by keyword with relevance ranking.

    Uses SOSL for full-text search when available, falls back to SOQL LIKE queries.

    Args:
        query: Search keywords (natural language or specific terms).
        language: Article language filter (default en_US).
        limit: Maximum results to return (1-25, default 10).
    """
    limit = max(1, min(25, limit))

    try:
        sf = _get_sf_client()

        # Try SOSL first for relevance-ranked results
        search_method = "sosl"
        try:
            safe_query = query.replace("'", "\\'").replace("\\", "\\\\")
            sosl = (
                f"FIND {{{safe_query}}} IN ALL FIELDS "
                f"RETURNING KnowledgeArticleVersion("
                f"{ARTICLE_FIELDS} "
                f"WHERE PublishStatus = 'Online' "
                f"AND Language = '{language}' "
                f"AND IsLatestVersion = true "
                f"ORDER BY LastPublishedDate DESC "
                f"LIMIT {limit})"
            )
            records = sf.search(sosl)
        except SalesforceClientError:
            # Fallback to SOQL
            search_method = "soql"
            safe_query = query.replace("'", "\\'")
            soql = (
                f"SELECT {ARTICLE_FIELDS} FROM KnowledgeArticleVersion "
                f"WHERE Title LIKE '%{safe_query}%' "
                f"AND PublishStatus = 'Online' "
                f"AND Language = '{language}' "
                f"AND IsLatestVersion = true "
                f"ORDER BY LastPublishedDate DESC "
                f"LIMIT {limit}"
            )
            records = sf.query(soql)

        articles = [_record_to_article(r).model_dump() for r in records]

        return {
            "articles": articles,
            "total_count": len(articles),
            "search_method": search_method,
        }

    except SalesforceClientError as e:
        error_msg = str(e.message) if hasattr(e, "message") else str(e)
        if "Knowledge" in error_msg or "KnowledgeArticle" in error_msg:
            return ErrorResponse(
                code="KNOWLEDGE_DISABLED",
                message="Salesforce Knowledge is not enabled or accessible. "
                "Please contact your Salesforce admin to enable Knowledge.",
            ).model_dump()
        return e.to_error_response()


@mcp.tool()
def get_article_by_id(
    article_id: str,
) -> dict[str, Any]:
    """Retrieve the full content of a Knowledge Article by its version ID.

    Args:
        article_id: Knowledge Article Version ID.
    """
    try:
        sf = _get_sf_client()

        # Query the article with body content
        soql = (
            f"SELECT {ARTICLE_FIELDS} FROM KnowledgeArticleVersion "
            f"WHERE Id = '{article_id}' "
            f"AND PublishStatus = 'Online' "
            f"AND IsLatestVersion = true "
            f"LIMIT 1"
        )
        records = sf.query(soql)

        if not records:
            return ErrorResponse(
                code="NOT_FOUND",
                message=f"Knowledge article '{article_id}' not found or not published.",
            ).model_dump()

        article = _record_to_article(records[0], include_body=True)

        return {"article": article.model_dump()}

    except SalesforceClientError as e:
        error_msg = str(e.message) if hasattr(e, "message") else str(e)
        if "Knowledge" in error_msg:
            return ErrorResponse(
                code="KNOWLEDGE_DISABLED",
                message="Salesforce Knowledge is not enabled or accessible.",
            ).model_dump()
        return e.to_error_response()
