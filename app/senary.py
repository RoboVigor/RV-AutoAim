import autoaim
import cv2
w = 1024
h = 768
camera = autoaim.Camera(0)
camera.snapshot('00:00:00', '00:20:00', 200, 'data/capture/')
