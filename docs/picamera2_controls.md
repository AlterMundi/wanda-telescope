# Picamera2 Controls Reference for IMX477 Sensor

This document provides a comprehensive reference for all available picamera2 controls when using the IMX477 sensor (Raspberry Pi High Quality Camera) with the WANDA telescope system.

## Overview

The picamera2 library provides access to various camera controls through the `set_controls()` method. The available controls depend on the specific camera hardware and firmware. This document focuses on controls available for the IMX477 sensor used in the WANDA telescope system.

## Currently Implemented Controls

The WANDA telescope system currently uses the following essential controls:

### Exposure Controls
- **`ExposureTime`** - Exposure time in microseconds
  - Range: 31µs to 230s (IMX477 specifications)
  - Usage: Controls how long the sensor is exposed to light
  - Example: `{"ExposureTime": 1000000}` (1 second exposure)

- **`AnalogueGain`** - Sensor analogue gain
  - Range: 1.0 to 16.0 (IMX477 specifications)
  - Usage: Amplifies the signal before digital processing
  - Example: `{"AnalogueGain": 8.0}` (8x gain)

### System Controls
- **`AeEnable`** - Automatic exposure control
  - Values: `True`/`False`
  - Usage: Disable for manual exposure control
  - Example: `{"AeEnable": False}` (manual mode)

- **`FrameDurationLimits`** - Frame duration limits
  - Format: `(min_microseconds, max_microseconds)`
  - Usage: Set minimum and maximum frame durations
  - Example: `{"FrameDurationLimits": (100, 230_000_000)}` (100µs to 230s)

## Additional Available Controls

### Autofocus Controls
- **`AfMode`** - Autofocus mode
  - Values: `Manual`, `Auto`, `Continuous`
  - Usage: Control autofocus behavior
  - Example: `{"AfMode": "Manual"}`

- **`AfTrigger`** - Trigger autofocus
  - Values: `Start`, `Cancel`
  - Usage: Trigger autofocus cycle when in Auto mode
  - Example: `{"AfTrigger": "Start"}`

- **`AfSpeed`** - Autofocus speed
  - Values: `Normal`, `Fast`
  - Usage: Control how fast autofocus operates
  - Example: `{"AfSpeed": "Fast"}`

- **`LensPosition`** - Manual lens position
  - Range: Varies by lens (typically 0.0 to 10.0 diopters)
  - Usage: Set manual focus position
  - Example: `{"LensPosition": 2.5}`

### White Balance Controls
- **`AwbEnable`** - Automatic white balance
  - Values: `True`/`False`
  - Usage: Enable/disable automatic white balance
  - Example: `{"AwbEnable": False}` (manual white balance)

- **`AwbMode`** - White balance mode
  - Values: `Auto`, `Incandescent`, `Tungsten`, `Fluorescent`, `Indoor`, `Daylight`, `Cloudy`, `Custom`
  - Usage: Set white balance mode
  - Example: `{"AwbMode": "Daylight"}`

- **`ColourGains`** - Color gains
  - Format: `(red_gain, blue_gain)`
  - Usage: Manual color balance control
  - Example: `{"ColourGains": (1.2, 1.8)}`

- **`ColourTemperature`** - Color temperature
  - Range: 2000K to 10000K
  - Usage: Set color temperature in Kelvin
  - Example: `{"ColourTemperature": 5500}`

### Image Quality Controls
- **`Brightness`** - Image brightness
  - Range: -1.0 to 1.0
  - Usage: Adjust image brightness
  - Example: `{"Brightness": 0.1}`

- **`Contrast`** - Image contrast
  - Range: 0.0 to 2.0
  - Usage: Adjust image contrast
  - Example: `{"Contrast": 1.2}`

- **`Saturation`** - Color saturation
  - Range: 0.0 to 2.0
  - Usage: Adjust color saturation
  - Example: `{"Saturation": 1.1}`

- **`Sharpness`** - Image sharpness
  - Range: 0.0 to 16.0
  - Usage: Adjust image sharpness
  - Example: `{"Sharpness": 2.0}`

### Digital Processing Controls
- **`DigitalGain`** - Digital gain
  - Range: 1.0 to 16.0
  - Usage: Additional gain after analogue gain
  - Example: `{"DigitalGain": 2.0}`

- **`NoiseReductionMode`** - Noise reduction
  - Values: `Off`, `Fast`, `HighQuality`, `Minimal`, `ZSL`
  - Usage: Control noise reduction algorithms
  - Example: `{"NoiseReductionMode": "HighQuality"}`

### Advanced Controls
- **`ScalerCrop`** - Scaler crop region
  - Format: `(x, y, width, height)`
  - Usage: Crop the image region
  - Example: `{"ScalerCrop": (0, 0, 1920, 1080)}`

- **`SensorBlackLevels`** - Sensor black level
  - Format: `(r, gr, gb, b)` or single value
  - Usage: Adjust sensor black level offsets
  - Example: `{"SensorBlackLevels": (64, 64, 64, 64)}`

## Usage Examples

### Basic Exposure Control
```python
camera.set_controls({
    "ExposureTime": 1000000,  # 1 second
    "AnalogueGain": 4.0,      # 4x gain
    "AeEnable": False          # Manual mode
})
```

### Astrophotography Setup
```python
camera.set_controls({
    "ExposureTime": 30000000,     # 30 seconds
    "AnalogueGain": 8.0,          # High gain for faint objects
    "AeEnable": False,            # Manual exposure
    "AwbEnable": False,           # Manual white balance
    "NoiseReductionMode": "Off",  # Disable noise reduction
    "DigitalGain": 1.0            # No additional digital gain
})
```

### Manual Focus Control
```python
camera.set_controls({
    "AfMode": "Manual",
    "LensPosition": 2.5,          # Focus at 2.5 diopters
    "AfTrigger": "Cancel"         # Cancel any ongoing autofocus
})
```

### Custom White Balance
```python
camera.set_controls({
    "AwbEnable": False,
    "AwbMode": "Custom",
    "ColourGains": (1.2, 1.8),    # Red and blue gains
    "ColourTemperature": 5500     # Daylight temperature
})
```

## Querying Available Controls

To see what controls are available on your specific camera setup:

```python
from picamera2 import Picamera2

camera = Picamera2()
camera.start()

# Get all available controls
controls = camera.camera_controls
print(f"Available controls: {len(controls)}")

for control_name, control_info in controls.items():
    control_id, control_details = control_info
    print(f"{control_name}:")
    print(f"  Type: {control_details.type}")
    if hasattr(control_details, 'min'):
        print(f"  Min: {control_details.min}")
    if hasattr(control_details, 'max'):
        print(f"  Max: {control_details.max}")
    if hasattr(control_details, 'default'):
        print(f"  Default: {control_details.default}")
    print()

camera.stop()
camera.close()
```

## Control Validation

The WANDA telescope system includes validation for critical controls:

```python
# Example from pi_camera.py
def set_exposure_us(self, us, gain=None):
    # Validate exposure time against sensor limits
    exp_limits = self.camera.camera_controls['ExposureTime']
    us = max(exp_limits.min, min(us, exp_limits.max))
    
    # Validate gain against sensor limits
    gain_limits = self.camera.camera_controls['AnalogueGain']
    gain = max(gain_limits.min, min(gain, gain_limits.max))
    
    self.camera.set_controls({
        "ExposureTime": us,
        "AnalogueGain": gain
    })
```

## Best Practices for Astrophotography

1. **Disable Auto Modes**: Always set `AeEnable` and `AwbEnable` to `False` for consistent results
2. **Use Manual Focus**: Set `AfMode` to `Manual` and control focus with `LensPosition`
3. **Optimize Gain**: Use `AnalogueGain` first, then `DigitalGain` if needed
4. **Disable Noise Reduction**: Set `NoiseReductionMode` to `Off` for raw sensor data
5. **Consistent White Balance**: Use manual `ColourGains` or `ColourTemperature` for consistent color

## Troubleshooting

### Control Not Available
If a control is not available, check:
- Camera hardware compatibility
- Firmware version
- Driver installation

### Control Values Out of Range
The system automatically clamps values to valid ranges:
- Exposure time: 31µs to 230s (IMX477)
- Analogue gain: 1.0 to 16.0 (IMX477)
- Other controls have sensor-specific limits

### Performance Impact
Some controls may affect performance:
- High `DigitalGain` values can reduce frame rates
- `NoiseReductionMode` processing adds latency
- `ScalerCrop` can improve performance by reducing data

## References

- [Picamera2 Documentation](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)
- [Libcamera Controls](https://libcamera.org/docs.html)
- [IMX477 Sensor Datasheet](https://www.sony-semicon.co.jp/products/IS/industry/IMX477.html)
- [WANDA Telescope Project](https://github.com/your-repo/wanda-telescope)

## Version History

- **v1.0** - Initial documentation for IMX477 sensor
- **v1.1** - Added astrophotography best practices
- **v1.2** - Updated with WANDA telescope implementation details
