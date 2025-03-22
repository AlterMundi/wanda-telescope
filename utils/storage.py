"""
Storage utilities for Wanda astrophotography system.
Handles file storage locations and management.
"""
import os
import logging
import config

logger = logging.getLogger(__name__)

def get_capture_dir():
    """
    Determine the best location for storing capture files.
    Prefers USB drive if available, falls back to home directory.
    
    Returns:
        str: Path to the capture directory
    """
    # Check USB drives first
    if os.path.exists(config.USB_BASE):
        usb_mounts = [d for d in os.listdir(config.USB_BASE) 
                     if os.path.isdir(os.path.join(config.USB_BASE, d))]
        
        if usb_mounts:
            # Use the first USB drive found
            usb_path = os.path.join(config.USB_BASE, usb_mounts[0], config.CAPTURE_SUBDIR)
            try:
                os.makedirs(usb_path, exist_ok=True)
                logger.info(f"Using USB storage at {usb_path}")
                return usb_path
            except Exception as e:
                logger.error(f"Could not create directory on USB: {e}")
    
    # Fall back to home directory
    try:
        os.makedirs(config.HOME_BASE, exist_ok=True)
        logger.info(f"Using home storage at {config.HOME_BASE}")
        return config.HOME_BASE
    except Exception as e:
        logger.error(f"Could not create home directory: {e}")
        # Last resort - use current directory
        return "."

def get_free_space(path):
    """
    Get free space at the given path.
    
    Args:
        path (str): Path to check
    
    Returns:
        int: Free space in bytes
    """
    try:
        stats = os.statvfs(path)
        return stats.f_frsize * stats.f_bavail
    except Exception as e:
        logger.error(f"Error checking free space at {path}: {e}")
        return 0

def format_space(bytes_value):
    """
    Format bytes into human readable form.
    
    Args:
        bytes_value (int): Bytes to format
    
    Returns:
        str: Formatted string (e.g. "1.2 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024 or unit == 'TB':
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024