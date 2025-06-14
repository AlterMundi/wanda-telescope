from .base import AbstractMount
from .implementations.pi_mount import PiMount
from .implementations.mock_mount import MockMount

class MountFactory:
    """Factory class for creating mount instances."""

    @staticmethod
    def create_mount():
        """Create and return a mount instance based on the environment."""
        try:
            import RPi.GPIO as GPIO
            return PiMount()
        except ImportError:
            return MockMount() 