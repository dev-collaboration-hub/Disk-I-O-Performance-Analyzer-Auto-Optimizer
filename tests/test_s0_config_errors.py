"""Tests for S0 deterministic configuration and structured errors."""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from core.collectors import CollectorError as CollectorErrorFromCollectors
from core.configuration import DEFAULT_CONFIG, RuntimeConfig, load_json_config
from core.errors import (
    CollectorError,
    CollectorErrorCode,
    ConfigurationError,
    CoreError,
    CoreErrorCode,
)


class RuntimeConfigTests(unittest.TestCase):
    def test_defaults_are_explicit_and_safe(self) -> None:
        self.assertEqual(DEFAULT_CONFIG.schema_version, 1)
        self.assertEqual(DEFAULT_CONFIG.sample_interval_seconds, 1.0)
        self.assertFalse(DEFAULT_CONFIG.automatic_actions_enabled)

    def test_config_is_immutable(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            DEFAULT_CONFIG.sample_interval_seconds = 9.0  # type: ignore[misc]

    def test_same_values_have_same_fingerprint_regardless_of_mapping_order(self) -> None:
        first = RuntimeConfig.from_mapping(
            {
                "sample_interval_seconds": 0.5,
                "history_retention_records": 500,
            }
        )
        second = RuntimeConfig.from_mapping(
            {
                "history_retention_records": 500,
                "sample_interval_seconds": 0.5,
            }
        )

        self.assertEqual(first, second)
        self.assertEqual(first.fingerprint(), second.fingerprint())
        self.assertEqual(len(first.fingerprint()), 64)

    def test_unknown_fields_are_rejected_in_sorted_form(self) -> None:
        with self.assertRaises(ConfigurationError) as context:
            RuntimeConfig.from_mapping({"zeta": 1, "alpha": 2})

        self.assertEqual(context.exception.code, CoreErrorCode.INVALID_CONFIG)
        self.assertEqual(context.exception.operation, "load_config")
        self.assertEqual(context.exception.context, (("fields", "alpha,zeta"),))

    def test_invalid_values_are_not_silently_coerced(self) -> None:
        with self.assertRaises(ConfigurationError):
            RuntimeConfig.from_mapping({"sample_interval_seconds": "1.0"})
        with self.assertRaises(ConfigurationError):
            RuntimeConfig.from_mapping({"automatic_actions_enabled": 1})
        with self.assertRaises(ConfigurationError):
            RuntimeConfig.from_mapping({"history_retention_records": 0})

    def test_explicit_json_file_loads_without_environment_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scratch-config.json"
            path.write_text(
                json.dumps(
                    {
                        "sample_interval_seconds": 0.25,
                        "refresh_interval_seconds": 1.5,
                        "automatic_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            config = load_json_config(path)

        self.assertEqual(config.sample_interval_seconds, 0.25)
        self.assertEqual(config.refresh_interval_seconds, 1.5)
        self.assertFalse(config.automatic_actions_enabled)

    def test_non_object_json_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scratch-config.json"
            path.write_text("[]", encoding="utf-8")

            with self.assertRaises(ConfigurationError) as context:
                load_json_config(path)

        self.assertEqual(context.exception.operation, "parse_config")


class CoreErrorTests(unittest.TestCase):
    def test_error_context_is_sorted_and_retryability_is_explicit(self) -> None:
        error = CoreError(
            CoreErrorCode.CONTRACT_VIOLATION,
            "normalize_sample",
            "sample does not satisfy contract",
            retryable=False,
            context={"z": 2, "a": 1},
        )

        self.assertEqual(error.context, (("a", 1), ("z", 2)))
        self.assertFalse(error.retryable)

    def test_collector_error_contract_remains_compatible(self) -> None:
        self.assertIs(CollectorErrorFromCollectors, CollectorError)

        error = CollectorError(
            CollectorErrorCode.UNAVAILABLE,
            "read_native_counter",
            "counter is temporarily unavailable",
            retryable=True,
        )

        self.assertIsInstance(error, CoreError)
        self.assertTrue(error.retryable)
        self.assertEqual(error.code, CollectorErrorCode.UNAVAILABLE)


if __name__ == "__main__":
    unittest.main()
