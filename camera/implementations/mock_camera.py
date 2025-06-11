"""Mock camera implementation for development and testing."""

from ..base import AbstractCamera
from typing import Tuple, Optional, Any

class MockCamera(AbstractCamera):
    """A mock camera implementation for development and testing."""
    
    def __init__(self):
        self._connected = False
        self._preview_active = False
    
    def initialize(self) -> None:
        """Initialize the mock camera."""
        self._connected = True
    
    def capture_image(self) -> Tuple[bool, Optional[Any]]:
        """Simulate capturing an image."""
        if not self._connected:
            return False, None
        # Return a simple test pattern or placeholder
        return True, None
    
    def start_preview(self) -> bool:
        """Simulate starting preview."""
        if not self._connected:
            return False
        self._preview_active = True
        return True
    
    def stop_preview(self) -> None:
        """Simulate stopping preview."""
        self._preview_active = False
    
    def close(self) -> None:
        """Clean up mock camera resources."""
        self._connected = False
        self._preview_active = False
    
    @property
    def is_connected(self) -> bool:
        """Check if mock camera is 'connected'."""
        return self._connected 