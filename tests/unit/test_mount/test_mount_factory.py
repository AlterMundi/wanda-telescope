"""Unit tests for mount factory."""
import pytest
from unittest.mock import Mock, patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from mount.factory import MountFactory
from mount.implementations.mock_mount import MockMount

class TestMountFactory:
    def test_create_mount_returns_mock_when_gpio_unavailable(self):
        """Test that factory returns mock mount when RPi.GPIO is not available."""
        with patch.dict("sys.modules", {"RPi": None, "RPi.GPIO": None}):
            mount = MountFactory.create_mount()
            assert isinstance(mount, MockMount)
