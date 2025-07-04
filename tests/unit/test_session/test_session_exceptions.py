"""Unit tests for session exceptions."""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from session.exceptions import (
    SessionError,
    SessionAlreadyRunningError,
    SessionNotFoundError,
    SessionConfigurationError
)

class TestSessionExceptions:
    """Test cases for session exceptions."""
    
    def test_session_error_inheritance(self):
        """Test that SessionError is the base exception."""
        assert issubclass(SessionAlreadyRunningError, SessionError)
        assert issubclass(SessionNotFoundError, SessionError)
        assert issubclass(SessionConfigurationError, SessionError)
    
    def test_session_already_running_error(self):
        """Test SessionAlreadyRunningError can be raised and caught."""
        with pytest.raises(SessionAlreadyRunningError) as exc_info:
            raise SessionAlreadyRunningError("A session is already running")
        
        assert str(exc_info.value) == "A session is already running"
        assert isinstance(exc_info.value, SessionError)
    
    def test_session_not_found_error(self):
        """Test SessionNotFoundError can be raised and caught."""
        with pytest.raises(SessionNotFoundError) as exc_info:
            raise SessionNotFoundError("Session 'test' not found")
        
        assert str(exc_info.value) == "Session 'test' not found"
        assert isinstance(exc_info.value, SessionError)
    
    def test_session_configuration_error(self):
        """Test SessionConfigurationError can be raised and caught."""
        with pytest.raises(SessionConfigurationError) as exc_info:
            raise SessionConfigurationError("Invalid session configuration")
        
        assert str(exc_info.value) == "Invalid session configuration"
        assert isinstance(exc_info.value, SessionError)
    
    def test_exception_hierarchy(self):
        """Test that all session exceptions inherit from Exception."""
        assert issubclass(SessionError, Exception)
        assert issubclass(SessionAlreadyRunningError, Exception)
        assert issubclass(SessionNotFoundError, Exception)
        assert issubclass(SessionConfigurationError, Exception) 