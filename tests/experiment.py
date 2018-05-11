# -*- coding: utf-8 -*-
import sys
sys.path.append('../')
import numpy as np
import cv2
from autoaim.huaq import AimMat

cap = cv2.VideoCapture(1) # 0 for computer camera; 1 for usb camera

i = 0

while(True):
    ret, frame = cap.read()
    #cv2.imshow('you', frame) # show source image
    autoaim = AimMat(frame)
    autoaim.showoff('miao '*3)
    if len(autoaim) > 0:
        dir = '../data_experiment/'
        key = str(i)
        cv2.imwrite(dir+key+'.jpg', frame)
        print('------')
        print('Image: ', key+'.jpg')
        print('found lamps: ',len(autoaim.lamps))
        print('found pairs: ',len(autoaim))
        print('Area: ', autoaim.areas)
        print('Center: ', autoaim.centers)
        i += 1
        if cv2.waitKey(100) & 0xFF == 27:
                break
    else:
        if cv2.waitKey(10) & 0xFF == 27:
                    break
cap.release()
cv2.destroyAllWindows()