"""OAuth 2.0 authentication helpers for Salesforce.

Supports Authorization Code flow (per-user delegated auth) and token refresh.
Per research.md Section 4.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class OAuthTokens:
    """OAuth token set from Salesforce."""

    access_token: str
    refresh_token: str
    instance_url: str
    token_type: str = "Bearer"
    issued_at: str = ""
    id_url: str = ""


class SalesforceAuthError(Exception):
    """Raised when Salesforce authentication fails."""


def build_authorization_url(
    instance_url: str,
    consumer_key: str,
    callback_url: str,
    state: str = "",
) -> str:
    """Build the Salesforce OAuth authorization URL.

    Args:
        instance_url: Salesforce instance URL (e.g., https://mycompany.my.salesforce.com)
        consumer_key: Connected App consumer key
        callback_url: OAuth redirect URI
        state: Optional state parameter for CSRF protection

    Returns:
        Full authorization URL for user redirect.
    """
    base = f"{instance_url}/services/oauth2/authorize"
    params = {
        "response_type": "code",
        "client_id": consumer_key,
        "redirect_uri": callback_url,
        "scope": "api refresh_token openid",
    }
    if state:
        params["state"] = state

    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{base}?{query}"


async def exchange_code_for_tokens(
    instance_url: str,
    consumer_key: str,
    consumer_secret: str,
    callback_url: str,
    authorization_code: str,
) -> OAuthTokens:
    """Exchange an authorization code for OAuth tokens.

    Args:
        instance_url: Salesforce instance URL
        consumer_key: Connected App consumer key
        consumer_secret: Connected App consumer secret
        callback_url: OAuth redirect URI (must match)
        authorization_code: Code from the authorization callback

    Returns:
        OAuthTokens with access_token and refresh_token.

    Raises:
        SalesforceAuthError: If the token exchange fails.
    """
    token_url = f"{instance_url}/services/oauth2/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": consumer_key,
        "client_secret": consumer_secret,
        "redirect_uri": callback_url,
        "code": authorization_code,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=payload)

    if response.status_code != 200:
        error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        raise SalesforceAuthError(
            f"Token exchange failed: {error_data.get('error_description', response.text)}"
        )

    data: dict[str, Any] = response.json()
    return OAuthTokens(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token", ""),
        instance_url=data["instance_url"],
        token_type=data.get("token_type", "Bearer"),
        issued_at=data.get("issued_at", ""),
        id_url=data.get("id", ""),
    )


async def refresh_access_token(
    instance_url: str,
    consumer_key: str,
    consumer_secret: str,
    refresh_token: str,
) -> OAuthTokens:
    """Refresh an expired access token using a refresh token.

    Args:
        instance_url: Salesforce instance URL
        consumer_key: Connected App consumer key
        consumer_secret: Connected App consumer secret
        refresh_token: Valid refresh token

    Returns:
        OAuthTokens with new access_token (refresh_token may be reused).

    Raises:
        SalesforceAuthError: If the refresh fails.
    """
    token_url = f"{instance_url}/services/oauth2/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": consumer_key,
        "client_secret": consumer_secret,
        "refresh_token": refresh_token,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=payload)

    if response.status_code != 200:
        error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        raise SalesforceAuthError(
            f"Token refresh failed: {error_data.get('error_description', response.text)}"
        )

    data: dict[str, Any] = response.json()
    return OAuthTokens(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token", refresh_token),
        instance_url=data.get("instance_url", instance_url),
        token_type=data.get("token_type", "Bearer"),
        issued_at=data.get("issued_at", ""),
        id_url=data.get("id", ""),
    )


async def revoke_token(instance_url: str, token: str) -> bool:
    """Revoke an access or refresh token.

    Args:
        instance_url: Salesforce instance URL
        token: The token to revoke

    Returns:
        True if revocation succeeded.
    """
    revoke_url = f"{instance_url}/services/oauth2/revoke"

    async with httpx.AsyncClient() as client:
        response = await client.post(revoke_url, data={"token": token})

    if response.status_code == 200:
        logger.info("Token revoked successfully")
        return True

    logger.warning("Token revocation failed: %s", response.text)
    return False
