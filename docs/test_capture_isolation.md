# Test Capture Directory Isolation

## Problem

Previously, when running tests that involved camera operations, captured images were being saved to a `tests/captures/` directory, which would:

1. Create test artifacts that could be accidentally committed to git
2. Pollute the test environment with real files
3. Interfere with the main project's capture directory structure

## Solution

### 1. Temporary Test Directories

Tests now use temporary directories for captures that are automatically cleaned up:

```python
@pytest.fixture
def test_capture_dir():
    """Create a temporary directory for test captures that gets cleaned up."""
    temp_dir = tempfile.mkdtemp(prefix="test_captures_")
    yield temp_dir
    # Clean up the temporary directory after tests
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: Could not clean up test capture directory {temp_dir}: {e}")
```

### 2. Flexible Camera Constructors

All camera implementations now accept an optional `capture_dir` parameter:

```python
# Before
camera = MockCamera()  # Always used "captures" directory

# After
camera = MockCamera(capture_dir=test_capture_dir)  # Uses test directory
```

### 3. Updated Test Fixtures

Test fixtures automatically provide the test capture directory:

```python
@pytest.fixture
def mock_camera(test_capture_dir):
    """Create a mock camera instance with test capture directory."""
    camera = MockCamera(capture_dir=test_capture_dir)
    return camera
```

### 4. Enhanced .gitignore

Added patterns to prevent test captures from being committed:

```gitignore
# Test captures
tests/captures/
test_captures_*/
capture_*.jpg
video_*.mp4
```

## Benefits

1. **Isolation**: Test captures don't interfere with the main project
2. **Cleanup**: Temporary directories are automatically removed
3. **Flexibility**: Tests can use different capture directories
4. **Git Safety**: Test artifacts won't be accidentally committed
5. **Reproducibility**: Tests start with a clean state each time

## Usage

### Running Tests

Tests automatically use isolated capture directories:

```bash
pytest tests/unit/test_camera/test_capture_directory.py -v
```

### Manual Testing

For manual testing or development, you can specify a custom capture directory:

```python
from camera.implementations.mock_camera import MockCamera
import tempfile

# Create a temporary directory
test_dir = tempfile.mkdtemp(prefix="my_test_")

# Use it with the camera
camera = MockCamera(capture_dir=test_dir)
camera.initialize()
camera.capture_still()

# Clean up when done
import shutil
shutil.rmtree(test_dir)
```

### Demonstration

Run the demo script to see the isolation in action:

```bash
python tests/demo_capture_isolation.py
```

## Implementation Details

### Files Modified

1. `tests/conftest.py` - Added `test_capture_dir` fixture
2. `camera/implementations/mock_camera.py` - Added `capture_dir` parameter
3. `camera/implementations/pi_camera.py` - Added `capture_dir` parameter  
4. `camera/implementations/usb_camera.py` - Added `capture_dir` parameter
5. `.gitignore` - Added test capture patterns
6. `tests/unit/test_camera/test_capture_directory.py` - New test file
7. `tests/demo_capture_isolation.py` - Demonstration script

### Backward Compatibility

The changes are backward compatible:
- If no `capture_dir` is provided, cameras default to `"captures"`
- Existing code continues to work without modification
- Only tests benefit from the new isolation features 