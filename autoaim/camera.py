# -*- coding: utf-8 -*-
import cv2
import numpy as np
import sys
import os
from autoaim import helpers
import importlib

device_manager = None


class Camera():
    def __init__(self, source, method=None):
        if method is None:
            if type(source) is str:
                method = 'video'
                source = helpers.main_dir+'data/'+source
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
            global device_manager
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
            capture.ExposureTime.set(1000)
            capture.BalanceRatio.set(1.1250)
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
            try:
                raw_image = capture.data_stream[0].get_image()
                new_img = raw_image.convert('RGB').get_numpy_array()[..., ::-1]
                return (True, new_img)
            except:
                return (False, None)

    def release(self):
        self.capture.release()


if __name__ == '__main__':
    camera = Camera(0, 'daheng')
    camera.init((1280, 1024))
    helpers.showoff(camera.get_image()[1])
