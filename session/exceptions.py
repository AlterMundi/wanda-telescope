"""Session-related exceptions for the Wanda Telescope project."""

class SessionError(Exception):
    """Base exception for all session-related errors."""
    pass

class SessionAlreadyRunningError(SessionError):
    """Raised when attempting to start a session while another is already running."""
    pass

class SessionNotFoundError(SessionError):
    """Raised when attempting to access a session that doesn't exist."""
    pass

class SessionConfigurationError(SessionError):
    """Raised when session configuration is invalid."""
    pass 