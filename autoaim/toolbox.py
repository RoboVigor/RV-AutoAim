# -*- coding: utf-8 -*-
"""Image Processing Toolbox

Author:
    tccoin
"""

import cv2
import numpy as np
from toolz import pipe, curry
from autoaim import helpers, AttrDict


class Lamp(AttrDict):
    def __init__(self, contour):
        super().__init__({
            'contour': contour
        })


class Pair(AttrDict):
    def __init__(self, left, right):
        super().__init__({
            'left': left,
            'right': right
        })


class ToolboxConfig(AttrDict):
    def __init__(self, config={}):
        _config = {
            'proceed_channel': lambda c: cv2.subtract(c[2], c[0]),  # (b,g,r)
            'binary_threshold_value': None,
            'binary_threshold_scale': lambda t: (255-t) * 0.1+t,
            'rect_area_threshold': (32, 16384),
            'point_area_threshold': (32, 8192),
            'max_contour_len': 100,
            'features': ['bounding_rects', 'rotated_rects', 'greyscales_and_point_areas', 'ellipses']
        }
        _config.update(config)
        super().__init__(_config)


class Toolbox():

    def __init__(self, config=ToolboxConfig()):
        """receive a image with rgb channel"""
        self.config = config
        self.mat = AttrDict()
        self.data = AttrDict()

    # ===================
    # CV
    # ===================

    def split_channels(self, mat):
        '''mat -> grayscale_mat'''
        channals = cv2.split(mat)
        self.mat.grayscale = self.config.proceed_channel(channals)
        return self.mat.grayscale

    def preprocess(self, grayscale_mat):
        '''grayscale_mat -> grayscale_mat'''
        kernel = np.ones((5, 5), np.uint8)
        self.mat.grayscale = cv2.dilate(
            grayscale_mat, kernel, iterations=1)
        return self.mat.grayscale

    def binarize(self, grayscale_mat):
        '''grayscale_mat -> binary_mat'''
        if self.config.binary_threshold_value is None:
            ret = cv2.threshold(grayscale_mat, 0, 255, cv2.THRESH_OTSU)[0]
        else:
            ret = self.config.binary_threshold_value
        t = self.config.binary_threshold_scale(ret)
        self.mat.binary = cv2.threshold(
            grayscale_mat, t, 255, cv2.THRESH_BINARY)[1]
        return self.mat.binary

    def find_contours(self, binary_mat):
        '''binary_mat -> binary_mat (lamps, contours)'''
        contours = cv2.findContours(
            binary_mat, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[1]
        lamps = [Lamp(x) for x in contours]
        ################
        #  NEED UPDATE #
        ################
        max_contour_len = self.config.max_contour_len
        if len(contours) > max_contour_len:
            self.data.lamps = lamps[0:max_contour_len]
        else:
            self.data.lamps = lamps
        return binary_mat

    def calc_features(self, mat):
        methods = {
            'bounding_rects': lambda x: self.calc_bounding_rects(x),
            'rotated_rects': lambda x: self.calc_rotated_rects(x),
            'greyscales_and_point_areas': lambda x: self.calc_greyscales_and_point_areas(x),
            'ellipses': lambda x: self.calc_ellipses(x),
        }
        for feature in self.config.features:
            methods[feature](mat)
        return mat

    def calc_bounding_rects(self, mat):
        '''lamp.contour -> lamp.bounding_rect, lamp.bounding_rect_area, lamp.bounding_rect_ratio'''
        lamps = self.data.lamps
        for lamp in lamps:
            rect = cv2.boundingRect(lamp.contour)
            x, y, w, h = rect
            lamp.bounding_rect = rect
            lamp.bounding_rect_area = int(w * h)
            lamp.bounding_rect_ratio = w/h
        threshold = range(*self.config.rect_area_threshold)
        self.data.lamps = [
            x for x in lamps if x.bounding_rect_area in threshold]
        return mat

    def calc_rotated_rects(self, mat):
        '''lamp.contour -> lamp.rotated_rect'''
        lamps = self.data.lamps
        for lamp in lamps:
            rect = cv2.minAreaRect(lamp.contour)
            lamp.rotated_rect = rect
            _, (w, h), a = rect
            lamp.rotated_rect_angle = a+180 if w > h else a+90
        return mat

    def calc_greyscales_and_point_areas(self, mat):
        '''mat -> lamp.greyscale, lamp.point_areas'''
        lamps = self.data.lamps
        for lamp in lamps:
            x, y, w, h = lamp.bounding_rect
            roi = np.zeros_like(mat)
            cv2.drawContours(roi, [lamp.contour], -1, color=255, thickness=-1)
            roi = roi[y:y+h, x:x+w]
            pts = np.where(roi == 255)
            pts = mat[pts[0], pts[1]]
            point_area = len(pts)
            greyscale = sum(pts) / point_area
            lamp.point_area = point_area
            lamp.greyscale = greyscale
        threshold = range(*self.config.point_area_threshold)
        self.data.lamps = [x for x in lamps if x.point_area in threshold]
        return mat

    def calc_ellipses(self, mat):
        '''lamp.contour -> lamp.ellipse'''
        lamps = self.data.lamps
        lamps = [x for x in lamps if len(x.contour) >= 6]
        for lamp in lamps:
            lamp.ellipse = cv2.fitEllipse(lamp.contour)
        return mat

    def match_pairs(self, mat):
        '''lamp -> pair'''
        pairs = []
        lamps = sorted(self.data.lamps, key=lambda x: x.bounding_rect[0])
        for i in range(len(lamps)):
            for j in range(i+1, len(lamps)):
                left = lamps[i]
                right = lamps[j]
                pair = Pair(left, right)
                (x1, y1, w1, h1), (x2, y2, w2,
                                   h2) = left.bounding_rect, right.bounding_rect
                if y1 > y2:
                    y1 = right.bounding_rect[1]
                    h1 = right.bounding_rect[3]
                    y2 = left.bounding_rect[1]
                    h2 = left.bounding_rect[3]
                pair.bounding_rect = (x1, y1, x2-x1+w2, y2-y1+h2)
                x, y, w, h = pair.bounding_rect
                if w/h > 8 or w/h < 2:
                    continue
                pair.ratio = w/((h1+h2)/2)
                pair.x = [
                    abs(pair.ratio-3.17),
                    abs(pair.ratio-6.2),
                    abs(y2-y1)/200,
                    abs(w2-w1)/200,
                    abs(h2-h1)/200,
                    abs(left.rotated_rect_angle-90)/90,
                    abs(right.rotated_rect_angle-90)/90,
                    abs(left.rotated_rect_angle-right.rotated_rect_angle)/90
                ]
                pair.anglex = [
                    (y2-y1)/200,
                    (left.rotated_rect_angle-90)/90,
                    (right.rotated_rect_angle-90)/90,
                    w1/w2,
                    w2/w1,
                ]
                pairs += [pair]
        self.data.pairs = pairs
        return mat

    # ===================
    # Helper
    # ===================


if __name__ == '__main__':
    for i in range(135, 250, 1):
        img_url = 'data/test12/img{}.jpg'.format(i)
        print('Load {}'.format(img_url))
        img = helpers.load(img_url)
        toolbox = Toolbox()
        pipe(img,
             toolbox.split_channels,
             helpers.peek,
             toolbox.preprocess,
             helpers.peek,
             toolbox.binarize,
             toolbox.find_contours,
             toolbox.calc_features,
             toolbox.match_pairs,
             helpers.showoff,
             )
        print(toolbox.data.pairs)
