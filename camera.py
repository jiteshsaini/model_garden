"""
camera.py - frames from a USB webcam or the Raspberry Pi camera, as OpenCV
expects them.

On Raspberry Pi OS Buster the ribbon camera looked like an ordinary V4L2
device, so cv2.VideoCapture(0) was enough. Since Bullseye /dev/video0 is the
raw Bayer receiver: OpenCV opens it and read() never returns a frame. The
ribbon camera is read through picamera2 instead.

    import camera
    cap = camera.VideoCapture()
    ok, frame = cap.read()      # BGR
"""

import time
import cv2

# Set to True if the picture comes out upside down.
ROTATE_180 = False

CAM_INDEXES = 5           # /dev/video0..4, searched for a USB webcam
SIZE = (640, 480)
WARMUP_SECONDS = 0.5      # let exposure and white balance settle


class VideoCapture:

    def __init__(self, size=SIZE):
        self.backend = None
        self._cap = None
        self._picam = None
        self.size = size
        if not self._try_usb() and not self._try_picamera2():
            print("camera: no USB webcam delivered a frame and no Raspberry Pi camera was found")

    def _try_usb(self):
        # A Pi numbers its own camera and codec blocks as /dev/video* too, so a
        # webcam is rarely on video0. Prove each one by reading a frame:
        # unicam opens without error and never delivers.
        for index in range(CAM_INDEXES):
            cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
            if cap.isOpened():
                for _ in range(3):
                    ok, frame = cap.read()
                    if ok and frame is not None:
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.size[0])
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.size[1])
                        self._cap = cap
                        self.backend = "usb"
                        print("camera: USB webcam on /dev/video%d" % index)
                        return True
                    time.sleep(0.1)
            cap.release()
        return False

    def _try_picamera2(self):
        try:
            from picamera2 import Picamera2
            from libcamera import Transform
            p = Picamera2()
            flip = 1 if ROTATE_180 else 0
            # picamera2 calls it RGB888, but the bytes are in B,G,R order,
            # which is what OpenCV wants.
            p.configure(p.create_video_configuration(
                main={"size": self.size, "format": "RGB888"},
                transform=Transform(hflip=flip, vflip=flip)))
            p.start()
            time.sleep(WARMUP_SECONDS)
            self._picam = p
            self.backend = "picamera2"
            print("camera: Raspberry Pi camera")
            return True
        except Exception as e:
            print("camera: picamera2 -", e)
            return False

    def isOpened(self):
        return self.backend is not None

    def read(self):
        if self.backend == "usb":
            ok, frame = self._cap.read()
            if ok and ROTATE_180:
                frame = cv2.flip(frame, -1)
            return ok, frame
        if self.backend == "picamera2":
            try:
                return True, self._picam.capture_array()
            except Exception as e:
                print("camera:", e)
        return False, None

    def release(self):
        if self._cap is not None:
            self._cap.release()
        if self._picam is not None:
            try:
                self._picam.stop()
                self._picam.close()
            except Exception:
                pass
        self._cap = self._picam = self.backend = None
