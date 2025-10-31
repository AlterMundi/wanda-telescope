# Camera State Restoration

## Overview

The Wanda Telescope system now includes automatic camera state restoration functionality. When the application starts, it saves the original camera state, and when the application closes, it restores the camera to its original state.

## Problem Solved

Previously, when users changed camera parameters (exposure time, gain, night vision mode, etc.) during a session and then closed the application, those changes would remain on the camera hardware. This could cause issues when the camera is used by other applications or when the system is restarted.

## Solution

The system now automatically:

1. **Saves Original State**: When the camera is initialized, the system saves all camera parameters including:
   - Exposure time
   - Gain/ISO settings
   - Night vision mode and intensity
   - Digital gain settings
   - Hardware-specific settings (brightness, exposure mode, etc.)

2. **Restores Original State**: When the application closes (either normally or due to a signal), the system:
   - Restores all saved parameters to their original values
   - Applies the restored settings to the camera hardware
   - Ensures the camera is in the same state as when the application started

## Implementation Details

### Base Camera Class (`camera/base.py`)

Added two new methods to the `AbstractCamera` class:

- `save_original_state()`: Saves the current camera state for later restoration
- `restore_original_state()`: Restores the camera to its original state

### Camera Implementations

Each camera implementation includes hardware-specific state restoration:

- **USB Camera**: Restores brightness, exposure mode, gain, and exposure settings
- **Pi Camera**: Restores picamera2 controls and exposure mode
- **Mock Camera**: Simple state restoration for testing

### Application Integration (`main.py`)

The main application:

1. Calls `camera.save_original_state()` after camera initialization
2. Calls `camera.restore_original_state()` before cleanup in signal handlers and exception handling

## Benefits

- **Non-intrusive**: Camera returns to its original state when the app closes
- **Compatible**: Other applications can use the camera without interference
- **Reliable**: Works across different camera types (USB, Pi Camera, Mock)
- **Automatic**: No user intervention required

## Testing

The functionality is tested through:

- Unit tests for the main application signal handling
- Integration tests for camera parameter management
- Manual testing with real camera hardware

## Usage

No changes are required for users. The functionality is automatic and transparent. When you:

1. Start the Wanda application
2. Change camera settings during your session
3. Close the application

The camera will automatically return to its original state. 