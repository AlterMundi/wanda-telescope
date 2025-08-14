import os
from .base import AbstractMount
from .implementations.mock_mount import MockMount

class MountFactory:
    """Factory class for creating mount instances."""

    @staticmethod
    def create_mount():
        """Create and return a mount instance based on the environment."""
        # Check for explicit mock mount request
        if os.environ.get('MOCK_MOUNT'):
            return MockMount()
            
        try:
            import RPi.GPIO as GPIO
            from .implementations.pi_mount import PiMount
            return PiMount()
        except (ImportError, RuntimeError) as e:
            # ImportError: RPi.GPIO not available
            # RuntimeError: GPIO peripheral issues (like SOC base address)
            return MockMount() 