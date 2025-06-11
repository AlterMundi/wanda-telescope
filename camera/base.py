from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any

class AbstractCamera(ABC):
    """Abstract base class defining the interface for all camera implementations."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the camera hardware and prepare it for capture."""
        pass
    
    @abstractmethod
    def capture_image(self) -> Tuple[bool, Optional[Any]]:
        """Capture a single image from the camera.
        
        Returns:
            Tuple[bool, Optional[Any]]: Success status and image data if successful
        """
        pass
    
    @abstractmethod
    def start_preview(self) -> bool:
        """Start the camera preview if supported.
        
        Returns:
            bool: True if preview started successfully
        """
        pass
    
    @abstractmethod
    def stop_preview(self) -> None:
        """Stop the camera preview."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Clean up and release camera resources."""
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the camera is currently connected and available.
        
        Returns:
            bool: True if camera is connected and ready
        """
        pass 