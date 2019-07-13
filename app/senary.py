import autoaim
import cv2
import os
w = 1280
h = 720
camera = autoaim.Camera(0)
capture = camera.capture
capture.set(3, w)
capture.set(4, h)
capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
capture.set(cv2.CAP_PROP_EXPOSURE, 0)
print(os.path.abspath(__file__ + '/../../data/capture'))
camera.snapshot('00:00:00', '00:20:00', 200,
                os.path.abspath(__file__ + '/../../data/capture')+'/')
