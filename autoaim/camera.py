# -*- coding: utf-8 -*-
import cv2
import numpy as np
import sys
import os
from autoaim import helpers


class Camera():
    def __init__(self, source):
        self.source = source
        self.capture = cv2.VideoCapture(source)
        if type(source) is int:
            self.__camera = True

    def snapshot(self, start, stop, interval, save_to):
        '''
        start: "hour:minute:second"
        stop : "hour:minute:second"
        interval: 1000(ms)
        save_to: url
        '''
        capture = self.capture

        if self.__camera:
            capture.set(cv2.CAP_PROP_FPS, 30)
            start = self.__parse_time(start)
            stop = self.__parse_time(stop)
            for i in range(int((stop-start)*1000/interval)):
                success, img = capture.read()
                if success:
                    helpers.showoff(img, timeout=interval, update=True)
                    cv2.imwrite(save_to+str(i)+'.jpeg', img)
        else:
            fps = round(capture.get(cv2.CAP_PROP_FPS))
            start = self.__parse_time(start) * fps
            stop = self.__parse_time(stop) * fps
            step = int(interval / 1000 * fps)
            for i in range(start, stop, step):
                capture.set(cv2.CAP_PROP_POS_FRAMES, i)
                success, img = capture.read()
                if success:
                    helpers.showoff(img, timeout=interval, update=True)
                    cv2.imwrite(save_to+str(i)+'.jpeg', img)

    def release(self):
        self.capture.release()

    def __parse_time(self, str):
        t = np.array([int(x) for x in str.split(':')])
        w = np.array([3600, 60, 1])
        return t.dot(w).item(0)


if __name__ == '__main__':
    cam = Camera(0)
    cam.snapshot('00:00:00', '00:00:05', 1000, 'data/capture/')
