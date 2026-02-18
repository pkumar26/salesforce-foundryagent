"""Salesforce REST API client wrapper.

Wraps simple-salesforce with per-user auth, SOQL query helper,
API rate tracking, and write-back confirmation protocol.
Per research.md Section 5.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from simple_salesforce import Salesforce, SalesforceError

# Maximum records returned by any single query to prevent memory issues
MAX_QUERY_RESULTS = 2000

logger = logging.getLogger(__name__)

# Rate limit thresholds
RATE_LIMIT_WARNING_PERCENT = 0.80
API_VERSION = "62.0"


@dataclass
class ApiUsageTracker:
    """Track Salesforce API usage per session."""

    calls_made: int = 0
    session_start: float = field(default_factory=time.time)
    daily_limit: int = 100_000  # Default Enterprise edition
    warning_threshold: float = RATE_LIMIT_WARNING_PERCENT

    def record_call(self) -> None:
        """Record an API call."""
        self.calls_made += 1

    @property
    def usage_percent(self) -> float:
        """Current usage as a percentage of daily limit."""
        return (self.calls_made / self.daily_limit) * 100 if self.daily_limit > 0 else 0

    @property
    def is_warning(self) -> bool:
        """True if usage exceeds warning threshold."""
        return self.usage_percent >= (self.warning_threshold * 100)

    @property
    def is_exceeded(self) -> bool:
        """True if usage has exceeded the daily limit."""
        return self.calls_made >= self.daily_limit

    def get_status(self) -> dict[str, Any]:
        """Return usage status dict."""
        return {
            "calls_made": self.calls_made,
            "daily_limit": self.daily_limit,
            "usage_percent": round(self.usage_percent, 1),
            "is_warning": self.is_warning,
            "is_exceeded": self.is_exceeded,
        }


class SalesforceClientError(Exception):
    """Base error for Salesforce client operations."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_error_response(self) -> dict[str, Any]:
        """Convert to MCP error response format."""
        result: dict[str, Any] = {"error": {"code": self.code, "message": self.message}}
        if self.details:
            result["error"]["details"] = self.details
        return result


class WriteBackConfirmationError(Exception):
    """Raised when a write operation needs user confirmation."""

    def __init__(self, operation: str, details: dict[str, Any]) -> None:
        self.operation = operation
        self.details = details
        super().__init__(f"Write-back confirmation required for {operation}")


class SalesforceClient:
    """Wrapper around simple-salesforce with rate tracking and error handling.

    Each instance represents a per-user authenticated session.
    """

    def __init__(
        self,
        instance_url: str,
        access_token: str,
        api_version: str = API_VERSION,
    ) -> None:
        """Initialize client with per-user credentials.

        Args:
            instance_url: Salesforce instance URL
            access_token: OAuth access token for the user
            api_version: Salesforce REST API version
        """
        self._instance_url = instance_url
        self._access_token = access_token
        self._api_version = api_version
        self._usage = ApiUsageTracker()

        try:
            self._sf = Salesforce(
                instance_url=instance_url,
                session_id=access_token,
                version=api_version,
            )
        except SalesforceError as e:
            raise SalesforceClientError("AUTH_ERROR", f"Failed to connect to Salesforce: {e}") from e

    @property
    def usage(self) -> ApiUsageTracker:
        """Access the API usage tracker."""
        return self._usage

    def _check_rate_limit(self) -> dict[str, Any] | None:
        """Check rate limit status and return warning if needed."""
        if self._usage.is_exceeded:
            raise SalesforceClientError(
                "RATE_LIMIT_EXCEEDED",
                "Salesforce API daily limit exceeded. Please try again later.",
                self._usage.get_status(),
            )
        if self._usage.is_warning:
            return {
                "warning": {
                    "code": "RATE_LIMIT_WARNING",
                    "message": f"API usage at {self._usage.usage_percent:.0f}% of daily limit.",
                    "details": self._usage.get_status(),
                }
            }
        return None

    def query(self, soql: str) -> list[dict[str, Any]]:
        """Execute a SOQL query and return records.

        Args:
            soql: SOQL query string

        Returns:
            List of record dicts.

        Raises:
            SalesforceClientError: On query failure or rate limiting.
        """
        self._check_rate_limit()
        self._usage.record_call()

        try:
            result = self._sf.query(soql)
            records: list[dict[str, Any]] = result.get("records", [])
            # Strip Salesforce metadata attributes
            for record in records:
                record.pop("attributes", None)
                # Recursively strip from nested objects
                for _key, value in list(record.items()):
                    if isinstance(value, dict):
                        value.pop("attributes", None)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                item.pop("attributes", None)
            return records
        except SalesforceError as e:
            error_msg = str(e)
            if "INSUFFICIENT_ACCESS" in error_msg or "INVALID_SESSION_ID" in error_msg:
                raise SalesforceClientError("AUTH_ERROR", f"Authentication failed: {error_msg}") from e
            if "REQUEST_LIMIT_EXCEEDED" in error_msg:
                raise SalesforceClientError("RATE_LIMIT_EXCEEDED", "Salesforce API rate limit exceeded.") from e
            if "QUERY_TOO_COMPLICATED" in error_msg:
                raise SalesforceClientError(
                    "QUERY_TOO_COMPLEX",
                    "Query is too complex. Try adding filters to narrow results.",
                ) from e
            raise SalesforceClientError("SF_API_ERROR", f"SOQL query failed: {error_msg}") from e

    def query_all(self, soql: str, *, max_results: int = MAX_QUERY_RESULTS) -> list[dict[str, Any]]:
        """Execute a SOQL query and return all records (handles pagination).

        Results are capped at max_results to prevent memory issues.

        Args:
            soql: SOQL query string
            max_results: Maximum records to return (default: 2000).

        Returns:
            List of all record dicts.
        """
        self._check_rate_limit()
        self._usage.record_call()

        try:
            result = self._sf.query_all(soql)
            records: list[dict[str, Any]] = result.get("records", [])
            for record in records:
                record.pop("attributes", None)
            # Safety cap to prevent OOM on large orgs
            if len(records) > max_results:
                logger.warning(
                    "query_all returned %d records, capping to %d", len(records), max_results
                )
                records = records[:max_results]
            return records
        except SalesforceError as e:
            raise SalesforceClientError("SF_API_ERROR", f"SOQL query failed: {e}") from e

    def search(self, sosl: str) -> list[dict[str, Any]]:
        """Execute a SOSL search and return results.

        Args:
            sosl: SOSL search string

        Returns:
            List of search result records.
        """
        self._check_rate_limit()
        self._usage.record_call()

        try:
            result = self._sf.search(sosl)
            records: list[dict[str, Any]] = result.get("searchRecords", [])
            for record in records:
                record.pop("attributes", None)
            return records
        except SalesforceError as e:
            raise SalesforceClientError("SF_API_ERROR", f"SOSL search failed: {e}") from e

    def create_record(
        self,
        sobject: str,
        data: dict[str, Any],
        *,
        confirmed: bool = False,
    ) -> dict[str, Any]:
        """Create a Salesforce record.

        Args:
            sobject: Salesforce object type (e.g., 'Case', 'Task')
            data: Record field values
            confirmed: Whether the user has confirmed this write operation

        Returns:
            Dict with id, success, and created fields.

        Raises:
            WriteBackConfirmationError: If confirmed=False for write operations.
            SalesforceClientError: On API failure.
        """
        if not confirmed:
            raise WriteBackConfirmationError(
                operation=f"create_{sobject.lower()}",
                details={"object": sobject, "data": data},
            )

        self._check_rate_limit()
        self._usage.record_call()

        try:
            sf_object = getattr(self._sf, sobject)
            result: dict[str, Any] = sf_object.create(data)
            logger.info("Created %s record: %s", sobject, result.get("id"))
            return result
        except SalesforceError as e:
            error_msg = str(e)
            if "INSUFFICIENT_ACCESS" in error_msg:
                raise SalesforceClientError(
                    "PERMISSION_DENIED",
                    f"Insufficient permissions to create {sobject}: {error_msg}",
                ) from e
            raise SalesforceClientError(
                "SF_API_ERROR", f"Failed to create {sobject}: {error_msg}"
            ) from e

    def update_record(
        self,
        sobject: str,
        record_id: str,
        data: dict[str, Any],
        *,
        confirmed: bool = False,
    ) -> bool:
        """Update a Salesforce record.

        Args:
            sobject: Salesforce object type
            record_id: Salesforce record ID (18-char)
            data: Field updates
            confirmed: Whether the user has confirmed this write operation

        Returns:
            True if update succeeded.

        Raises:
            WriteBackConfirmationError: If confirmed=False.
            SalesforceClientError: On API failure.
        """
        if not confirmed:
            raise WriteBackConfirmationError(
                operation=f"update_{sobject.lower()}",
                details={"object": sobject, "record_id": record_id, "data": data},
            )

        self._check_rate_limit()
        self._usage.record_call()

        try:
            sf_object = getattr(self._sf, sobject)
            sf_object.update(record_id, data)
            logger.info("Updated %s record: %s", sobject, record_id)
            return True
        except SalesforceError as e:
            error_msg = str(e)
            if "NOT_FOUND" in error_msg or "ENTITY_IS_DELETED" in error_msg:
                raise SalesforceClientError("NOT_FOUND", f"{sobject} record {record_id} not found.") from e
            if "INSUFFICIENT_ACCESS" in error_msg:
                raise SalesforceClientError(
                    "PERMISSION_DENIED",
                    f"Insufficient permissions to update {sobject}: {error_msg}",
                ) from e
            raise SalesforceClientError(
                "SF_API_ERROR", f"Failed to update {sobject}: {error_msg}"
            ) from e

    def get_record(self, sobject: str, record_id: str) -> dict[str, Any]:
        """Retrieve a single record by ID.

        Args:
            sobject: Salesforce object type
            record_id: Salesforce record ID

        Returns:
            Record dict.
        """
        self._check_rate_limit()
        self._usage.record_call()

        try:
            sf_object = getattr(self._sf, sobject)
            result: dict[str, Any] = sf_object.get(record_id)
            result.pop("attributes", None)
            return result
        except SalesforceError as e:
            error_msg = str(e)
            if "NOT_FOUND" in error_msg:
                raise SalesforceClientError("NOT_FOUND", f"{sobject} record {record_id} not found.") from e
            raise SalesforceClientError("SF_API_ERROR", f"Failed to retrieve {sobject}: {error_msg}") from e


def create_client(instance_url: str, access_token: str) -> SalesforceClient:
    """Factory function to create a SalesforceClient.

    Args:
        instance_url: Salesforce instance URL
        access_token: OAuth access token

    Returns:
        Configured SalesforceClient instance.
    """
    return SalesforceClient(instance_url=instance_url, access_token=access_token)
