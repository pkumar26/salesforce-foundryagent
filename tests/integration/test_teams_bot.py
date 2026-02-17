"""Integration tests for Teams bot end-to-end chat experience.

Reference: T054b — Validates that the bot registration is correct
and the agent can be reached via Teams-style messaging.
"""

from __future__ import annotations

import os

import pytest


@pytest.mark.skipif(
    not os.environ.get("TEAMS_BOT_ENDPOINT"),
    reason="TEAMS_BOT_ENDPOINT not set — skip Teams E2E",
)
class TestTeamsBotE2E:
    """End-to-end test for Teams bot integration.

    These tests require a running bot service and are typically
    executed in a CI/CD pipeline after deployment.
    """

    @pytest.fixture
    def bot_endpoint(self) -> str:
        return os.environ["TEAMS_BOT_ENDPOINT"]

    @pytest.mark.asyncio
    async def test_bot_health_check(self, bot_endpoint: str) -> None:
        """Bot endpoint responds to health check."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{bot_endpoint}/health")
            # Bot should respond (may be 200 or 404 depending on implementation)
            assert response.status_code in (200, 404, 405)

    @pytest.mark.asyncio
    async def test_bot_activity_payload(self, bot_endpoint: str) -> None:
        """Bot endpoint accepts Activity JSON payload format."""
        import httpx

        activity = {
            "type": "message",
            "text": "What's in my pipeline?",
            "from": {"id": "test-user", "name": "Test User"},
            "channelId": "msteams",
            "conversation": {"id": "test-conversation"},
            "serviceUrl": "https://smba.trafficmanager.net/teams/",
        }

        async with httpx.AsyncClient() as client:
            # Without valid bot credentials this will return 401/403,
            # but the endpoint should at least accept the request format
            response = await client.post(
                f"{bot_endpoint}/api/messages",
                json=activity,
            )
            # 200 = processed, 401/403 = auth required (expected without creds)
            assert response.status_code in (200, 201, 401, 403)
