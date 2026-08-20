"""Tests for the S0 platform boundary and collector contracts."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from core.collectors import (
    CollectorBundle,
    CollectorError,
    CollectorErrorCode,
    DiskCapacityCollector,
    DiskDiscoveryCollector,
    PlatformKind,
    detect_platform,
)
from core.models import DiskDevice, DiskSample


NOW = datetime(2026, 8, 20, tzinfo=timezone.utc)


class FakeDiscovery:
    platform = PlatformKind.WINDOWS

    def discover_devices(self) -> tuple[DiskDevice, ...]:
        return (
            DiskDevice(
                device_id="windows:disk0",
                platform=self.platform.value,
                name="Disk 0",
                mount_points=("C:\\",),
                fs_type="NTFS",
            ),
        )


class FakeCapacity:
    platform = PlatformKind.WINDOWS

    def collect_capacity(
        self,
        device: DiskDevice,
        *,
        timestamp: datetime,
    ) -> DiskSample:
        return DiskSample(
            device_id=device.device_id,
            timestamp=timestamp,
            total_bytes=1000,
            used_bytes=400,
            free_bytes=600,
        )


class FakeLinuxCapacity(FakeCapacity):
    platform = PlatformKind.LINUX


class CollectorContractTests(unittest.TestCase):
    def test_platform_detection_normalizes_supported_names(self) -> None:
        self.assertEqual(detect_platform("Windows"), PlatformKind.WINDOWS)
        self.assertEqual(detect_platform(" linux "), PlatformKind.LINUX)

    def test_platform_detection_rejects_unsupported_system(self) -> None:
        with self.assertRaises(CollectorError) as context:
            detect_platform("Darwin")

        self.assertEqual(context.exception.code, CollectorErrorCode.UNSUPPORTED)
        self.assertEqual(context.exception.operation, "detect_platform")

    def test_fake_collectors_satisfy_runtime_protocols(self) -> None:
        self.assertIsInstance(FakeDiscovery(), DiskDiscoveryCollector)
        self.assertIsInstance(FakeCapacity(), DiskCapacityCollector)

    def test_bundle_allows_staged_collector_implementation(self) -> None:
        bundle = CollectorBundle(
            platform=PlatformKind.WINDOWS,
            discovery=FakeDiscovery(),
            capacity=FakeCapacity(),
        )

        device = bundle.discovery.discover_devices()[0]
        sample = bundle.capacity.collect_capacity(device, timestamp=NOW)

        self.assertEqual(device.device_id, "windows:disk0")
        self.assertEqual(sample.total_bytes, 1000)
        self.assertIsNone(bundle.disk_io)
        self.assertIsNone(bundle.process_io)

    def test_bundle_rejects_cross_platform_collector_mix(self) -> None:
        with self.assertRaises(ValueError):
            CollectorBundle(
                platform=PlatformKind.WINDOWS,
                discovery=FakeDiscovery(),
                capacity=FakeLinuxCapacity(),
            )

    def test_collector_error_requires_operation_and_message(self) -> None:
        with self.assertRaises(ValueError):
            CollectorError(CollectorErrorCode.IO_ERROR, "", "failure")
        with self.assertRaises(ValueError):
            CollectorError(CollectorErrorCode.IO_ERROR, "read_disk", "")


if __name__ == "__main__":
    unittest.main()
