# -*- coding: utf-8 -*-
import cv2
import numpy as np
import sys
from autoaim import helpers


class Camera():
    def __init__(self, source):
        self.source = source
        self.capture = cv2.VideoCapture(source)

    def snapshot(self, start, stop, interval, save_to):
        '''
        start: "hour:minute:second"
        stop : "hour:minute:second"
        interval: 1000(ms)
        save_to: url
        '''
        capture = self.capture
        fps = round(capture.get(cv2.CAP_PROP_FPS))
        start = self.__parse_time(start) * fps
        stop = self.__parse_time(stop) * fps
        interval = int(interval / 1000 * fps)
        for i in range(start, stop, interval):
            capture.set(cv2.CAP_PROP_POS_FRAMES, i)
            success, img = capture.read()
            if success:
                # helpers.showoff(img)
                cv2.imwrite(save_to+str(i)+'.jpeg', img)

    def __parse_time(self, str):
        t = np.array([int(x) for x in str.split(':')])
        w = np.array([3600, 60, 1])
        return t.dot(w)


if __name__ == '__main__':
    cam = Camera('/home/link/Codes/RV-AutoAim/data/Rick.and.Morty.S03E07.mp4')
    cam.snapshot('00:01:00', '00:01:10', 500,
                 '/home/link/Codes/RV-AutoAim/data/capture/')
