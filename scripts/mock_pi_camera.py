from camera.implementations.pi_camera import PiCamera
import numpy as np

class MockPicamera:
    def __init__(self):
        self.actions = []
        self.started = True
        self.configure_fail = False
        self.start_fail = False
        self.capture_fail = False

    def stop(self):
        self.actions.append('stop')
        if not self.started:
            raise RuntimeError('already stopped')
        self.started = False

    def start(self):
        self.actions.append('start')
        if self.start_fail:
            raise RuntimeError('start failed')
        if self.started:
            raise RuntimeError('already started')
        self.started = True

    def configure(self, config):
        self.actions.append(('configure', config))
        if self.configure_fail:
            raise RuntimeError('configure failed')

    def capture_array(self):
        self.actions.append('capture_array')
        if self.capture_fail:
            raise RuntimeError('capture failed')
        return np.zeros((10,10,3), dtype=np.uint8)

class TestCamera(PiCamera):
    def __init__(self):
        super().__init__(capture_dir='/tmp')
        self.camera = MockPicamera()
        self.started = True

    def create_still_configuration(self):
        return {'still': True}

    def update_camera_settings(self):
        pass

    def create_preview_configuration(self):
        return {'preview': True}

cam = TestCamera()

print('=== success case ===')
cam.capture_file('/tmp/test.jpg')
print(cam.camera.actions)

print('=== start failure ===')
cam.camera.start_fail = True
try:
    cam.capture_file('/tmp/test.jpg')
except Exception as e:
    print('Exception', e)
print(cam.camera.actions)
