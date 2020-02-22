import cv2
import numpy as np
from autoaim import Toolbox
cap = cv2.VideoCapture(0)
cap.set(3, 1024)
cap.set(4, 768)


watching_point = None
toolbox = Toolbox()
camera_matrix = np.array(toolbox.config['camera_matrix'])
cx = camera_matrix[0, 2]
cy = camera_matrix[1, 2]


def setPoint(event, x, y, flags, param):
    global watching_point
    if event == cv2.EVENT_FLAG_LBUTTON:
        watching_point = (x, y)


while True:
    _, img = cap.read()
    # img = toolbox.undistort(img)

    img = toolbox.draw_target()((cx, cy))(img)
    img = toolbox.draw_target()((cx, cy-100))(img)
    img = toolbox.draw_target()((cx, cy+100))(img)
    img = toolbox.draw_target()((cx+100, cy))(img)
    img = toolbox.draw_target()((cx-100, cy))(img)
    cv2.imshow('angle', img)
    cv2.setMouseCallback('angle', setPoint)
    if watching_point:
        angle = toolbox.calc_point_angle(*watching_point)
        print(angle)
        watching_point = None
    cv2.waitKey(10)
