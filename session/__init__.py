"""Wanda Telescope Session Module

This module provides session-based capture functionality for taking multiple
images, enabling future image stacking capabilities.

Example usage:
    from session import SessionController
    
    # Create a session controller
    session_controller = SessionController(camera, mount)
    
    # Start a capture session
    session_controller.start_session(
        name="moon_sequence",
        total_images=10,
        use_current_settings=True,
        enable_tracking=True
    )
"""

from .controller import SessionController

__all__ = [
    'SessionController'
] 