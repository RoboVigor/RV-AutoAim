# -*- coding: utf-8 -*-
"""测试云台运动

Author:
"""

import autoaim
import cv2

seq = 0


def rotate(degree):
    global seq
    seq = (seq+1) % 256
    print(seq)
    packet = autoaim.telegram.pack(
        0x0401, [float(degree), 0.0, bytes([0])], seq=seq)
    autoaim.telegram.send(packet)
    cv2.waitKey(20)


while True:
    amplitude = 30
    for i in range(0, amplitude, 1):
        rotate(1)
    for i in range(amplitude, -1*amplitude, -1):
        rotate(-1)
    for i in range(0, amplitude, 1):
        rotate(-1)
    for i in range(amplitude, -1*amplitude, -1):
        rotate(1)
