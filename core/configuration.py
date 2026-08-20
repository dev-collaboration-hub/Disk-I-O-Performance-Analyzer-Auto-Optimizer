"""Deterministic configuration contract for the scratch implementation.

Configuration has no implicit environment-variable or legacy-settings lookup.
The same explicit input produces the same validated object and fingerprint.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Mapping

from .errors import ConfigurationError


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    """Small, explicit configuration surface shared by scratch milestones."""

    schema_version: int = 1
    sample_interval_seconds: float = 1.0
    refresh_interval_seconds: float = 2.0
    collector_timeout_seconds: float = 5.0
    history_retention_records: int = 10_000
    automatic_actions_enabled: bool = False

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ConfigurationError(
                "validate_config",
                "schema_version must be exactly 1",
                context={"schema_version": self.schema_version},
            )

        for name in (
            "sample_interval_seconds",
            "refresh_interval_seconds",
            "collector_timeout_seconds",
        ):
            value = getattr(self, name)
            if type(value) not in (int, float) or isinstance(value, bool) or value <= 0:
                raise ConfigurationError(
                    "validate_config",
                    f"{name} must be a positive number",
                    context={"field": name, "value": value},
                )

        if (
            type(self.history_retention_records) is not int
            or self.history_retention_records <= 0
        ):
            raise ConfigurationError(
                "validate_config",
                "history_retention_records must be a positive integer",
                context={"value": self.history_retention_records},
            )

        if type(self.automatic_actions_enabled) is not bool:
            raise ConfigurationError(
                "validate_config",
                "automatic_actions_enabled must be boolean",
                context={"value": str(self.automatic_actions_enabled)},
            )

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "RuntimeConfig":
        """Build from explicit values, rejecting unknown keys and coercion."""

        allowed = {field.name for field in fields(cls)}
        unknown = sorted(set(values) - allowed)
        if unknown:
            raise ConfigurationError(
                "load_config",
                "unknown configuration fields",
                context={"fields": ",".join(unknown)},
            )

        return cls(**dict(values))  # type: ignore[arg-type]

    def to_mapping(self) -> dict[str, object]:
        """Return a plain mapping in dataclass field order."""

        return asdict(self)

    def fingerprint(self) -> str:
        """Stable SHA-256 identity for this exact validated configuration."""

        encoded = json.dumps(
            self.to_mapping(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


DEFAULT_CONFIG = RuntimeConfig()


def load_json_config(path: str | Path) -> RuntimeConfig:
    """Load one explicit UTF-8 JSON object; no fallback sources are consulted."""

    config_path = Path(path)
    try:
        raw = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(
            "read_config",
            "unable to read configuration file",
            context={"path": str(config_path), "error": exc.__class__.__name__},
        ) from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            "parse_config",
            "configuration file is not valid JSON",
            context={"path": str(config_path), "line": exc.lineno, "column": exc.colno},
        ) from exc

    if not isinstance(data, dict):
        raise ConfigurationError(
            "parse_config",
            "configuration root must be a JSON object",
            context={"path": str(config_path)},
        )

    return RuntimeConfig.from_mapping(data)
