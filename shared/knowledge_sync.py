"""Knowledge Article Sync Pipeline.

Incrementally syncs Salesforce KnowledgeArticleVersion records
to an Azure AI Search index for RAG-based response grounding.

Supports:
- Full sync (initial load)
- Incremental sync (delta changes since last sync)
- Scheduled execution via cron or manual trigger
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Azure AI Search index schema for Knowledge Articles
KNOWLEDGE_INDEX_NAME = "salesforce-knowledge-articles"

KNOWLEDGE_INDEX_SCHEMA = {
    "name": KNOWLEDGE_INDEX_NAME,
    "fields": [
        {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
        {"name": "knowledgeArticleId", "type": "Edm.String", "filterable": True},
        {"name": "title", "type": "Edm.String", "searchable": True, "retrievable": True},
        {"name": "summary", "type": "Edm.String", "searchable": True, "retrievable": True},
        {"name": "articleBody", "type": "Edm.String", "searchable": True, "retrievable": True},
        {"name": "articleNumber", "type": "Edm.String", "filterable": True, "retrievable": True},
        {"name": "urlName", "type": "Edm.String", "retrievable": True},
        {
            "name": "publishStatus",
            "type": "Edm.String",
            "filterable": True,
            "retrievable": True,
        },
        {"name": "language", "type": "Edm.String", "filterable": True, "retrievable": True},
        {
            "name": "articleType",
            "type": "Edm.String",
            "filterable": True,
            "retrievable": True,
        },
        {
            "name": "lastModifiedDate",
            "type": "Edm.DateTimeOffset",
            "filterable": True,
            "sortable": True,
            "retrievable": True,
        },
        {
            "name": "lastPublishedDate",
            "type": "Edm.DateTimeOffset",
            "filterable": True,
            "sortable": True,
            "retrievable": True,
        },
        {
            "name": "versionNumber",
            "type": "Edm.Int32",
            "filterable": True,
            "retrievable": True,
        },
        {
            "name": "categoryGroups",
            "type": "Collection(Edm.String)",
            "filterable": True,
            "retrievable": True,
        },
    ],
}

# SOQL query for fetching KnowledgeArticleVersion records
KNOWLEDGE_SOQL_BASE = (
    "SELECT Id, KnowledgeArticleId, Title, Summary, "
    "ArticleNumber, UrlName, PublishStatus, Language, ArticleType, "
    "LastModifiedDate, LastPublishedDate, VersionNumber "
    "FROM KnowledgeArticleVersion "
    "WHERE PublishStatus = 'Online' AND Language = 'en_US' "
    "AND IsLatestVersion = true"
)


@dataclass
class SyncState:
    """Tracks the last successful sync timestamp for incremental syncs."""

    last_sync_timestamp: str | None = None
    total_synced: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_sync_timestamp": self.last_sync_timestamp,
            "total_synced": self.total_synced,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SyncState:
        return cls(
            last_sync_timestamp=data.get("last_sync_timestamp"),
            total_synced=data.get("total_synced", 0),
            errors=data.get("errors", []),
        )


def _load_sync_state(state_file: str) -> SyncState:
    """Load sync state from a JSON file."""
    if os.path.exists(state_file):
        with open(state_file) as f:
            return SyncState.from_dict(json.load(f))
    return SyncState()


def _save_sync_state(state: SyncState, state_file: str) -> None:
    """Save sync state to a JSON file."""
    with open(state_file, "w") as f:
        json.dump(state.to_dict(), f, indent=2)


def _build_soql_query(last_sync_timestamp: str | None = None) -> str:
    """Build SOQL query for knowledge articles, optionally filtering by last modified date."""
    query = KNOWLEDGE_SOQL_BASE
    if last_sync_timestamp:
        query += f" AND LastModifiedDate > {last_sync_timestamp}"
    query += " ORDER BY LastModifiedDate ASC"
    return query


def _transform_article_to_document(article: dict[str, Any]) -> dict[str, Any]:
    """Transform a Salesforce KnowledgeArticleVersion record to an Azure AI Search document."""
    return {
        "id": article["Id"],
        "knowledgeArticleId": article.get("KnowledgeArticleId", ""),
        "title": article.get("Title", ""),
        "summary": article.get("Summary", ""),
        "articleBody": "",  # Body requires a separate API call for rich text fields
        "articleNumber": article.get("ArticleNumber", ""),
        "urlName": article.get("UrlName", ""),
        "publishStatus": article.get("PublishStatus", ""),
        "language": article.get("Language", "en_US"),
        "articleType": article.get("ArticleType", ""),
        "lastModifiedDate": article.get("LastModifiedDate"),
        "lastPublishedDate": article.get("LastPublishedDate"),
        "versionNumber": article.get("VersionNumber", 1),
        "categoryGroups": [],
    }


async def ensure_search_index(
    search_endpoint: str,
    search_api_key: str,
) -> bool:
    """Create or update the Azure AI Search index for knowledge articles.

    Args:
        search_endpoint: Azure AI Search service endpoint.
        search_api_key: Azure AI Search admin API key.

    Returns:
        True if index was created/updated successfully, False otherwise.
    """
    import httpx

    url = f"{search_endpoint}/indexes/{KNOWLEDGE_INDEX_NAME}?api-version=2024-07-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": search_api_key,
    }

    async with httpx.AsyncClient() as client:
        # Check if index exists
        response = await client.get(url, headers=headers)
        if response.status_code == 404:
            # Create new index
            create_url = f"{search_endpoint}/indexes?api-version=2024-07-01"
            response = await client.post(
                create_url,
                headers=headers,
                json=KNOWLEDGE_INDEX_SCHEMA,
            )
            if response.status_code in (200, 201):
                logger.info("Created search index: %s", KNOWLEDGE_INDEX_NAME)
                return True
            logger.error("Failed to create index: %s", response.text)
            return False
        elif response.status_code == 200:
            logger.info("Search index already exists: %s", KNOWLEDGE_INDEX_NAME)
            return True
        else:
            logger.error("Failed to check index: %s", response.text)
            return False


async def upload_documents(
    documents: list[dict[str, Any]],
    search_endpoint: str,
    search_api_key: str,
    batch_size: int = 100,
) -> int:
    """Upload documents to Azure AI Search index in batches.

    Args:
        documents: List of documents to upload.
        search_endpoint: Azure AI Search service endpoint.
        search_api_key: Azure AI Search admin API key.
        batch_size: Number of documents per upload batch.

    Returns:
        Number of documents successfully uploaded.
    """
    import httpx

    url = f"{search_endpoint}/indexes/{KNOWLEDGE_INDEX_NAME}/docs/index?api-version=2024-07-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": search_api_key,
    }

    total_uploaded = 0

    async with httpx.AsyncClient() as client:
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            payload = {
                "value": [
                    {**doc, "@search.action": "mergeOrUpload"} for doc in batch
                ]
            }

            response = await client.post(url, headers=headers, json=payload)
            if response.status_code in (200, 207):
                result = response.json()
                succeeded = sum(
                    1 for r in result.get("value", []) if r.get("status", False)
                )
                total_uploaded += succeeded
                logger.info(
                    "Uploaded batch %d-%d: %d/%d succeeded",
                    i,
                    i + len(batch),
                    succeeded,
                    len(batch),
                )
            else:
                logger.error("Batch upload failed: %s", response.text)

    return total_uploaded


async def sync_knowledge_articles(
    sf_instance_url: str,
    sf_access_token: str,
    search_endpoint: str,
    search_api_key: str,
    full_sync: bool = False,
    state_file: str = ".knowledge_sync_state.json",
) -> SyncState:
    """Sync Salesforce Knowledge Articles to Azure AI Search.

    Args:
        sf_instance_url: Salesforce instance URL.
        sf_access_token: Salesforce OAuth access token.
        search_endpoint: Azure AI Search service endpoint.
        search_api_key: Azure AI Search admin API key.
        full_sync: If True, ignore last sync timestamp and sync all articles.
        state_file: Path to the sync state file.

    Returns:
        Updated SyncState with sync results.
    """
    from shared.salesforce_client import SalesforceClient

    state = _load_sync_state(state_file)

    if full_sync:
        state.last_sync_timestamp = None
        logger.info("Starting full sync of knowledge articles")
    else:
        logger.info(
            "Starting incremental sync since: %s",
            state.last_sync_timestamp or "beginning",
        )

    # Ensure search index exists
    index_ready = await ensure_search_index(search_endpoint, search_api_key)
    if not index_ready:
        state.errors.append("Failed to create/verify search index")
        _save_sync_state(state, state_file)
        return state

    # Query Salesforce for knowledge articles
    sf_client = SalesforceClient(
        instance_url=sf_instance_url, access_token=sf_access_token
    )
    query = _build_soql_query(state.last_sync_timestamp)

    try:
        results = sf_client.query_all(query)
    except Exception as e:
        state.errors.append(f"Salesforce query failed: {e}")
        _save_sync_state(state, state_file)
        return state

    records = results.get("records", [])
    logger.info("Found %d knowledge articles to sync", len(records))

    if not records:
        _save_sync_state(state, state_file)
        return state

    # Transform and upload
    documents = [_transform_article_to_document(r) for r in records]
    uploaded = await upload_documents(
        documents, search_endpoint, search_api_key
    )

    # Update state
    state.total_synced += uploaded
    state.last_sync_timestamp = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.000Z"
    )

    _save_sync_state(state, state_file)
    logger.info(
        "Sync complete: %d articles uploaded, %d total synced",
        uploaded,
        state.total_synced,
    )

    return state
