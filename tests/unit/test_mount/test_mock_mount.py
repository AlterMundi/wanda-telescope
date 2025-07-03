"""Unit tests for mock mount implementation."""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from mount.implementations.mock_mount import MockMount

class TestMockMount:
    def test_mock_mount_initialization(self):
        """Test mock mount initializes correctly."""
        mount = MockMount()
        assert mount.tracking is False
        assert mount.direction is True
        assert mount.speed == 1.0

    def test_start_stop_tracking(self):
        """Test starting and stopping tracking."""
        mount = MockMount()
        mount.initialize()
        mount.start_tracking()
        assert mount.tracking is True
        mount.stop_tracking()
        assert mount.tracking is False
