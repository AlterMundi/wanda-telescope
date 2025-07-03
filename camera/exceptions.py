class CameraError(Exception):
    """Base exception for all camera-related errors."""
    pass

class CameraInitializationError(CameraError):
    """Raised when camera fails to initialize."""
    pass

class CameraNotFoundError(CameraError):
    """Raised when no compatible camera is found."""
    pass

class CameraNotConnectedError(CameraError):
    """Raised when attempting to use a camera that is not connected."""
    pass

class CaptureError(CameraError):
    """Raised when image capture fails."""
    pass

class UnsupportedFeatureError(CameraError):
    """Raised when attempting to use a feature not supported by the camera."""
    pass 