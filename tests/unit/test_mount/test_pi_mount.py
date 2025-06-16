"""Unit tests for Pi mount implementation."""
import pytest
from unittest.mock import Mock, patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

class TestPiMount:
    def test_pi_mount_with_mocked_gpio(self, mock_gpio):
        """Test Pi mount with mocked GPIO."""
        from mount.implementations.pi_mount import PiMount
        mount = PiMount()
        assert hasattr(mount, "motor_pins")
        assert hasattr(mount, "tracking")
