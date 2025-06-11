import os
import platform
from typing import List, Dict, Any

def is_raspberry_pi() -> bool:
    """Check if the current system is a Raspberry Pi.
    
    Returns:
        bool: True if running on a Raspberry Pi
    """
    try:
        with open('/proc/device-tree/model', 'r') as f:
            return 'raspberry pi' in f.read().lower()
    except:
        return False

def get_available_cameras() -> List[Dict[str, Any]]:
    """Detect available cameras in the system.
    
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing camera information
    """
    cameras = []
    
    # Check for Raspberry Pi camera
    if is_raspberry_pi():
        try:
            import picamera2
            cameras.append({
                'type': 'pi_camera',
                'name': 'Raspberry Pi Camera',
                'interface': 'CSI',
                'available': True
            })
        except ImportError:
            pass
    
    # Check for USB cameras
    if platform.system() != "Windows":
        for i in range(10):  # Check first 10 possible video devices
            device = f"/dev/video{i}"
            if os.path.exists(device):
                cameras.append({
                    'type': 'usb_camera',
                    'name': f'USB Camera ({device})',
                    'device': device,
                    'interface': 'USB',
                    'available': True
                })
    
    return cameras

def get_preferred_camera() -> Dict[str, Any]:
    """Get the preferred camera based on availability and type.
    
    Returns:
        Dict[str, Any]: Information about the preferred camera
    """
    cameras = get_available_cameras()
    
    # Prefer Raspberry Pi camera if available
    pi_camera = next((cam for cam in cameras if cam['type'] == 'pi_camera'), None)
    if pi_camera:
        return pi_camera
    
    # Fall back to first USB camera
    usb_camera = next((cam for cam in cameras if cam['type'] == 'usb_camera'), None)
    if usb_camera:
        return usb_camera
    
    # Return mock camera configuration if no physical camera is available
    return {
        'type': 'mock_camera',
        'name': 'Mock Camera',
        'interface': 'Virtual',
        'available': True
    } 