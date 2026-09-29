"""
Configuration Management for Khronos Research System

Supports:
- Environment-based settings (development, staging, production)
- Configuration file loading (JSON, YAML)
- Environment variable overrides
- Customizable peer groups
- Metric configurations
- Logging settings
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum


class Environment(str, Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class KhronosConfig:
    """Central configuration management for Khronos system."""

    def __init__(self, env: Optional[str] = None, config_file: Optional[str] = None):
        """Initialize configuration.

        Args:
            env: Environment name (dev/staging/prod). Defaults to KHRONOS_ENV or 'development'
            config_file: Path to configuration JSON file. Defaults to config.json in project root
        """
        self.env: Environment = Environment(env or os.getenv("KHRONOS_ENV", "development"))
        self.config_file: Path = Path(config_file or "config.json")
        self._config: Dict[str, Any] = {}

        self._load_defaults()
        self._load_config_file()
        self._load_env_overrides()

    def _load_defaults(self) -> None:
        """Load default configuration values."""
        self._config = {
            "database": {
                "url": "sqlite:///khronos_research.db",
                "echo": False,
                "pool_size": 5,
            },
            "api": {
                "host": "localhost",
                "port": 5000,
                "debug": self.env == Environment.DEVELOPMENT,
            },
            "logging": {
                "level": "INFO" if self.env == Environment.PRODUCTION else "DEBUG",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "extraction": {
                "mock_mode": True,  # Use mock data instead of real PDF extraction
                "confidence_threshold": 0.7,
                "enable_caching": True,
            },
            "metrics": {
                "calculation_version": "fundamentals_v1",
                "cache_results": self.env != Environment.DEVELOPMENT,
            },
            "peer_groups": self._get_default_peer_groups(),
            "document_storage": {
                "base_path": "documents",
                "max_file_size_mb": 100,
                "allowed_types": ["pdf", "xlsx", "xls"],
            },
            "security": {
                "enable_authentication": self.env == Environment.PRODUCTION,
                "secret_key": os.getenv("KHRONOS_SECRET_KEY", "dev-secret-key-change-in-prod"),
            },
        }

    def _get_default_peer_groups(self) -> Dict[str, Dict[str, Any]]:
        """Get default peer group definitions."""
        return {
            "Fertilizer": {
                "name": "Fertilizer Sector Leaders",
                "description": "Major fertilizer manufacturers in Pakistan",
                "members": ["FFC", "EFERT", "FATIMA"],
                "sector": "Fertilizer",
            },
            "Cement": {
                "name": "Cement Manufacturers",
                "description": "Portland cement producers and suppliers",
                "members": ["LUCK", "FCCL", "DGKC", "MLCF"],
                "sector": "Cement",
            },
            "Banking": {
                "name": "Commercial Banks",
                "description": "Major commercial and retail banks",
                "members": ["MCB", "HBL"],
                "sector": "Banking",
            },
            "Energy": {
                "name": "Oil & Gas Exploration",
                "description": "E&P operators in Pakistan",
                "members": ["OGDC", "PPL", "PIOC"],
                "sector": "E&P",
            },
        }

    def _load_config_file(self) -> None:
        """Load configuration from JSON file if it exists."""
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, "r") as f:
                file_config = json.load(f)

            # Deep merge with defaults
            self._deep_merge(self._config, file_config)
        except Exception as e:
            print(f"Warning: Failed to load config file {self.config_file}: {e}")

    def _load_env_overrides(self) -> None:
        """Load configuration overrides from environment variables.

        Supports:
        - KHRONOS_DATABASE_URL
        - KHRONOS_LOG_LEVEL
        - KHRONOS_DEBUG
        """
        env_overrides = {
            "KHRONOS_DATABASE_URL": ["database", "url"],
            "KHRONOS_LOG_LEVEL": ["logging", "level"],
            "KHRONOS_DEBUG": ["api", "debug"],
            "KHRONOS_MOCK_MODE": ["extraction", "mock_mode"],
        }

        for env_var, config_path in env_overrides.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested(self._config, config_path, self._parse_env_value(value))

    @staticmethod
    def _parse_env_value(value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        if value.lower() in ("true", "1", "yes"):
            return True
        if value.lower() in ("false", "0", "no"):
            return False
        if value.isdigit():
            return int(value)
        return value

    @staticmethod
    def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep merge source config into target config."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                KhronosConfig._deep_merge(target[key], value)
            else:
                target[key] = value

    @staticmethod
    def _set_nested(config: Dict[str, Any], path: List[str], value: Any) -> None:
        """Set value in nested dictionary using path."""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.

        Args:
            key: Configuration key (e.g., 'database.url', 'api.port')
            default: Default value if key not found

        Returns:
            Configuration value

        Example:
            >>> config = KhronosConfig()
            >>> config.get("database.url")
            'sqlite:///khronos_research.db'
        """
        keys = key.split(".")
        current = self._config

        for k in keys:
            if isinstance(current, dict):
                current = current.get(k)
                if current is None:
                    return default
            else:
                return default

        return current

    def get_peer_groups(self) -> Dict[str, Dict[str, Any]]:
        """Get all peer group definitions.

        Returns:
            Dictionary of peer groups
        """
        return self._config.get("peer_groups", {})

    def get_peer_group(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific peer group definition.

        Args:
            name: Peer group name

        Returns:
            Peer group definition or None
        """
        return self.get_peer_groups().get(name)

    def add_peer_group(
        self,
        name: str,
        members: List[str],
        sector: str,
        group_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Add or update a peer group definition.

        Args:
            name: Peer group key (e.g., 'Fertilizer')
            members: List of company tickers
            sector: Sector name
            group_name: Display name for peer group
            description: Description of peer group
        """
        if "peer_groups" not in self._config:
            self._config["peer_groups"] = {}

        self._config["peer_groups"][name] = {
            "name": group_name or name,
            "description": description or f"{name} peer group",
            "members": members,
            "sector": sector,
        }

    def get_metrics_config(self) -> Dict[str, Any]:
        """Get metrics calculation configuration.

        Returns:
            Metrics configuration dictionary
        """
        return self._config.get("metrics", {})

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env == Environment.DEVELOPMENT

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env == Environment.PRODUCTION

    def save_to_file(self, filepath: Optional[str] = None) -> None:
        """Save current configuration to JSON file.

        Args:
            filepath: Path to save configuration. Defaults to config.json
        """
        path = Path(filepath or "config.json")
        with open(path, "w") as f:
            json.dump(self._config, f, indent=2, default=str)

    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"KhronosConfig(env={self.env.value})"


# Global configuration instance
_config: Optional[KhronosConfig] = None


def get_config(env: Optional[str] = None, config_file: Optional[str] = None) -> KhronosConfig:
    """Get or create global configuration instance.

    Args:
        env: Environment name (only used on first call)
        config_file: Configuration file path (only used on first call)

    Returns:
        Global KhronosConfig instance
    """
    global _config
    if _config is None:
        _config = KhronosConfig(env, config_file)
    return _config


def reset_config() -> None:
    """Reset global configuration instance (useful for testing)."""
    global _config
    _config = None
