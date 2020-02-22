# -*- coding: utf-8 -*-
import cv2
import numpy as np
import sys
import os
from autoaim import helpers
import importlib


class Camera():
    def __init__(self, source, method=None):
        if method is None:
            if type(source) is str:
                method = 'video'
            else:
                method = 'default'
        self.source = source
        self.method = method

    def init(self, resolution=None):
        if self.method == 'default' or self.method == 'video':
            capture = cv2.VideoCapture(self.source)
            if resolution is not None:
                capture.set(3, resolution[0])
                capture.set(4, resolution[1])
            if self.method == 'video':
                # load into memory
                frames = []
                while True:
                    suc, frame = capture.read()
                    if suc:
                        frames += [frame]
                    else:
                        break
                self.frames = frames
                self.count = 0
            self.capture = capture
        elif self.method == 'daheng':
            gx = importlib.import_module('gxipy')
            device_manager = gx.DeviceManager()
            dev_num, dev_info_list = device_manager.update_device_list()
            if dev_num == 0:
                sys.exit(1)
            str_index = dev_info_list[0].get("index")
            capture = device_manager.open_device_by_index(str_index)
            if resolution is not None:
                capture.Width.set(resolution[0])
                capture.Height.set(resolution[1])
            capture.stream_on()
            self.gx = gx
            self.capture = capture
        return self

    def get_image(self):
        capture = self.capture
        if self.method == 'default':
            return capture.read()
        elif self.method == 'video':
            self.count = (self.count+1) % len(self.frames)
            return (True, self.frames[self.count])
        elif self.method == 'daheng':
            raw_image = capture.data_stream[0].get_image()
            new_img = raw_image.convert('RGB').get_numpy_array()[..., ::-1]
            return (True, new_img)
            # try:
            # except:
            #     print('error when read image')
            #     return (False, None)

    def snapshot(self, start, stop, interval, save_to, width=1024, height=768):
        '''
        start: "hour:minute:second"
        stop : "hour:minute:second"
        interval: 1000(ms)
        save_to: url
        '''
        capture = self.capture

        if self.method == 'default':
            capture.set(cv2.CAP_PROP_FPS, 30)
            capture.set(3, width)
            capture.set(4, height)
            start = self.__parse_time(start)
            stop = self.__parse_time(stop)
            for i in range(int((stop-start)*1000/interval)):
                success, img = capture.read()
                if success:
                    helpers.showoff(img, timeout=interval, update=True)
                    cv2.imwrite(save_to+str(i)+'.jpeg', img)
        elif self.method == 'video':
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
    camera = Camera(0, 'daheng')
    camera.init((1280, 1024))
    helpers.showoff(camera.get_image()[1])
    # cam.snapshot('00:00:00', '00:01:00', 200, 'data/capture/')
