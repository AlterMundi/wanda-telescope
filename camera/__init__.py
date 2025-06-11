"""Wanda Telescope Camera Module

This module provides a unified interface for different camera implementations,
including Raspberry Pi Camera, USB cameras, and a mock implementation for
development and testing.

Example usage:
    from camera import CameraFactory
    
    # Auto-detect and create appropriate camera
    camera = CameraFactory.create_camera()
    
    # Or specify camera type
    camera = CameraFactory.create_camera('pi_camera')
    
    # Initialize and use
    camera.initialize()
    success, image = camera.capture_image()
"""

from .factory import CameraFactory
from .base import AbstractCamera
from .exceptions import (
    CameraError,
    CameraInitializationError,
    CameraNotFoundError,
    CameraNotConnectedError,
    CaptureError,
    UnsupportedFeatureError
)

__all__ = [
    'CameraFactory',
    'AbstractCamera',
    'CameraError',
    'CameraInitializationError',
    'CameraNotFoundError',
    'CameraNotConnectedError',
    'CaptureError',
    'UnsupportedFeatureError'
]
