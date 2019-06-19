import autoaim
import cv2
import time

print(cv2.__version__)

# global var
new_img = None
aim = True
ww = 640
hh = 360
fpscount = 0


def load_img():
    # set up camera
    global aim, new_img, ww, hh, fpscount


if __name__ == '__main__':
    camera = autoaim.Camera(1)
    capture = camera.capture
    capture.set(3, ww)
    capture.set(4, hh)
    capture.set(cv2.CAP_PROP_FPS, 120)
    # capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
    # capture.set(cv2.CAP_PROP_EXPOSURE, -9)
    # capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    last_timestamp = time.time()
    for i in range(1000):
        suc, new_img = capture.read()
        if i % 150 == 149:
            print("fps: ", 150/(time.time() - last_timestamp))
            last_timestamp = time.time()
