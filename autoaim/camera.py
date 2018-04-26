import numpy as np
import cv2
from autoaim import AimMat

cap = cv2.VideoCapture(0)

while(True):
    ret, frame = cap.read()
    cv2.imshow('you', frame)
    autoaim = AimMat(frame)
    autoaim.showoff('miao '*3)
    print('------')
    print('Found: ', len(autoaim))
    print('Area: ', autoaim.areas)
    print('Center: ', autoaim.centers)
    if cv2.waitKey(0) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()