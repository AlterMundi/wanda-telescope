from abc import ABC, abstractmethod

class AbstractMount(ABC):
    """Abstract base class defining the mount interface."""

    @abstractmethod
    def initialize(self):
        """Initialize the mount hardware."""
        pass

    @abstractmethod
    def start_tracking(self):
        """Start tracking with the mount."""
        pass

    @abstractmethod
    def stop_tracking(self):
        """Stop tracking with the mount."""
        pass

    @abstractmethod
    def cleanup(self):
        """Clean up mount resources."""
        pass 