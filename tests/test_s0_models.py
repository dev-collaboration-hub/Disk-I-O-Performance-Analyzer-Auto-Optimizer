from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

from core.models import (
    Diagnosis,
    DiskDevice,
    DiskSample,
    Evidence,
    OptimizationAction,
    ProcessIdentity,
    RiskLevel,
)


NOW = datetime(2026, 8, 20, tzinfo=timezone.utc)


class S0DomainModelTests(unittest.TestCase):
    def test_disk_device_is_immutable(self) -> None:
        device = DiskDevice(
            device_id="windows:physicaldrive0",
            platform="windows",
            name="PhysicalDrive0",
            mount_points=("C:\\",),
            fs_type="NTFS",
        )

        with self.assertRaises(FrozenInstanceError):
            device.name = "changed"  # type: ignore[misc]

    def test_disk_sample_accepts_partial_measurements(self) -> None:
        sample = DiskSample(
            device_id="disk0",
            timestamp=NOW,
            total_bytes=1_000,
            used_bytes=600,
            free_bytes=400,
        )

        self.assertIsNone(sample.read_bytes)
        self.assertEqual(sample.used_bytes, 600)

    def test_disk_sample_rejects_negative_counter(self) -> None:
        with self.assertRaises(ValueError):
            DiskSample(
                device_id="disk0",
                timestamp=NOW,
                read_bytes=-1,
            )

    def test_disk_sample_rejects_impossible_capacity(self) -> None:
        with self.assertRaises(ValueError):
            DiskSample(
                device_id="disk0",
                timestamp=NOW,
                total_bytes=100,
                used_bytes=101,
            )

    def test_naive_timestamp_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            DiskSample(
                device_id="disk0",
                timestamp=datetime(2026, 8, 20),
            )

    def test_process_identity_uses_start_time_to_survive_pid_reuse(self) -> None:
        first = ProcessIdentity(pid=42, started_at_ns=100, name="worker")
        reused = ProcessIdentity(pid=42, started_at_ns=200, name="worker")

        self.assertNotEqual(first, reused)

    def test_diagnosis_confidence_is_bounded(self) -> None:
        evidence = Evidence(
            key="disk.read_bytes_per_second",
            value=12_000,
            source="native.disk.sample",
            unit="B/s",
        )
        diagnosis = Diagnosis(
            code="SUSTAINED_IO_PRESSURE",
            timestamp=NOW,
            summary="Disk activity is sustained above the observed baseline.",
            confidence=0.75,
            evidence=(evidence,),
        )

        self.assertEqual(diagnosis.confidence, 0.75)

        with self.assertRaises(ValueError):
            Diagnosis(
                code="INVALID",
                timestamp=NOW,
                summary="invalid",
                confidence=1.1,
            )

    def test_action_contract_keeps_safety_metadata_explicit(self) -> None:
        action = OptimizationAction(
            action_type="LOWER_PROCESS_PRIORITY",
            timestamp=NOW,
            target="pid:42@100",
            rationale="Reduce verified sustained background I/O pressure.",
            reversible=True,
            requires_confirmation=True,
            parameters=(("priority", "below-normal"),),
        )

        self.assertTrue(action.reversible)
        self.assertTrue(action.requires_confirmation)

    def test_risk_levels_are_stable_string_values(self) -> None:
        self.assertEqual(RiskLevel.HIGH.value, "HIGH")


if __name__ == "__main__":
    unittest.main()
