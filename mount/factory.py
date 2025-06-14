from .base import AbstractMount
from .implementations.mock_mount import MockMount

class MountFactory:
    """Factory class for creating mount instances."""

    @staticmethod
    def create_mount():
        """Create and return a mount instance based on the environment."""
        try:
            import RPi.GPIO as GPIO
            from .implementations.pi_mount import PiMount
            return PiMount()
        except ImportError:
            return MockMount() 