"""Configuration loader for the Salesforce AI Assistant.

Loads environment variables from .env files and validates required configuration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class AzureConfig:
    """Azure AI Foundry configuration."""

    project_endpoint: str
    openai_deployment: str = "gpt-4o"
    key_vault_uri: str = ""
    app_insights_connection_string: str = ""


@dataclass(frozen=True)
class SalesforceConfig:
    """Salesforce connection configuration."""

    instance_url: str
    access_token: str = ""
    consumer_key: str = ""
    consumer_secret: str = ""
    callback_url: str = "https://localhost:8443/callback"
    api_version: str = "62.0"

    @property
    def has_oauth_credentials(self) -> bool:
        """Check if OAuth flow credentials are available."""
        return bool(self.consumer_key and self.consumer_secret)

    @property
    def has_direct_token(self) -> bool:
        """Check if a direct access token is available."""
        return bool(self.access_token)


@dataclass(frozen=True)
class McpConfig:
    """MCP server configuration."""

    transport: str = "stdio"
    crm_url: str = ""
    kb_url: str = ""
    hosting_mode: str = "none"


@dataclass(frozen=True)
class RiskThresholds:
    """Deal risk analysis thresholds from config/risk_thresholds.yaml."""

    stage_stagnation_days: int = 30
    inactivity_days: int = 14
    overdue_enabled: bool = True
    low_probability_threshold: int = 30
    late_stages: list[str] = field(
        default_factory=lambda: ["Negotiation/Review", "Proposal/Price Quote"]
    )
    minimum_amount_for_risk: float = 10000.0


@dataclass(frozen=True)
class AppConfig:
    """Root application configuration."""

    azure: AzureConfig
    salesforce: SalesforceConfig
    mcp: McpConfig
    risk_thresholds: RiskThresholds


class ConfigValidationError(Exception):
    """Raised when required configuration is missing or invalid."""


def _get_env(key: str, default: str = "") -> str:
    """Get an environment variable value."""
    return os.environ.get(key, default)


def _require_env(key: str) -> str:
    """Get a required environment variable, raising on missing."""
    value = os.environ.get(key, "")
    if not value:
        raise ConfigValidationError(f"Required environment variable '{key}' is not set.")
    return value


def load_risk_thresholds(config_path: str | Path | None = None) -> RiskThresholds:
    """Load risk thresholds from YAML configuration file.

    Args:
        config_path: Path to the risk_thresholds.yaml file.
                     Defaults to config/risk_thresholds.yaml in the project root.

    Returns:
        RiskThresholds with loaded values.
    """
    if config_path is None:
        # Default to project root / config / risk_thresholds.yaml
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config" / "risk_thresholds.yaml"

    config_path = Path(config_path)
    if not config_path.exists():
        return RiskThresholds()

    with open(config_path) as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    thresholds = data.get("risk_thresholds", {})
    return RiskThresholds(
        stage_stagnation_days=thresholds.get("stage_stagnation_days", 30),
        inactivity_days=thresholds.get("inactivity_days", 14),
        overdue_enabled=thresholds.get("overdue_enabled", True),
        low_probability_threshold=thresholds.get("low_probability_threshold", 30),
        late_stages=thresholds.get("late_stages", ["Negotiation/Review", "Proposal/Price Quote"]),
        minimum_amount_for_risk=float(thresholds.get("minimum_amount_for_risk", 10000)),
    )


def load_config(env_file: str | Path | None = None) -> AppConfig:
    """Load full application configuration from environment and config files.

    Args:
        env_file: Optional path to .env file. Defaults to .env in project root.

    Returns:
        AppConfig with all configuration sections loaded.

    Raises:
        ConfigValidationError: If required configuration is missing.
    """
    if env_file is None:
        project_root = Path(__file__).parent.parent
        env_file = project_root / ".env"

    load_dotenv(dotenv_path=str(env_file), override=False)

    azure = AzureConfig(
        project_endpoint=_require_env("AZURE_AI_PROJECT_ENDPOINT"),
        openai_deployment=_get_env("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        key_vault_uri=_get_env("AZURE_KEY_VAULT_URI"),
        app_insights_connection_string=_get_env("APPLICATIONINSIGHTS_CONNECTION_STRING"),
    )

    salesforce = SalesforceConfig(
        instance_url=_require_env("SF_INSTANCE_URL"),
        access_token=_get_env("SF_ACCESS_TOKEN"),
        consumer_key=_get_env("SF_CONSUMER_KEY"),
        consumer_secret=_get_env("SF_CONSUMER_SECRET"),
        callback_url=_get_env("SF_CALLBACK_URL", "https://localhost:8443/callback"),
    )

    if not salesforce.has_direct_token and not salesforce.has_oauth_credentials:
        raise ConfigValidationError(
            "Either SF_ACCESS_TOKEN or both SF_CONSUMER_KEY and SF_CONSUMER_SECRET must be set."
        )

    mcp = McpConfig(
        transport=_get_env("MCP_TRANSPORT", "stdio"),
        crm_url=_get_env("MCP_CRM_URL", ""),
        kb_url=_get_env("MCP_KB_URL", ""),
        hosting_mode=_get_env("HOSTING_MODE", "none"),
    )

    risk_thresholds = load_risk_thresholds()

    return AppConfig(
        azure=azure,
        salesforce=salesforce,
        mcp=mcp,
        risk_thresholds=risk_thresholds,
    )
