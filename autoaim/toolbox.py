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
            'camera_config': '',
            'target_color': 'red',
            'binary_threshold_value': None,
            'binary_threshold_scale': 0.1,
            'rect_area_threshold': (32, 16384),
            'hsv_lower_value': 46,
            'point_area_threshold': (32, 8192),
            'max_contour_len': 100,
            'features': ['bounding_rect', 'rotated_rect', 'ellipse', 'contour_feature']
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

    def start(self, mat):
        '''mat -> mat'''
        if hasattr(self.mat, 'original'):
            self.mat = AttrDict()
            self.data = AttrDict()
        self.mat.original = mat
        return self.mat.original

    def undistort(self, mat):
        '''mat -> mat'''
        return mat

    def split_channels(self, mat):
        '''mat -> grayscale_mat'''
        c = cv2.split(mat)
        mode = self.config.target_color
        if mode == 'red':
            grayscale = cv2.subtract(c[2], c[0])
        elif mode == 'blue':
            grayscale = cv2.subtract(c[0], c[2])
        elif mode == 'none':
            grayscale = c[0]
        # bgr
        self.mat.grayscale = grayscale
        return self.mat.grayscale

    def split_hsv(self, mat):
        '''mat -> binary_mat'''
        mode = self.config.target_color
        hsv = cv2.cvtColor(mat, cv2.COLOR_BGR2HSV)
        if mode == 'red':
            lower_hsv = np.array([0, 43, self.config.hsv_lower_value])
            upper_hsv = np.array([10, 255, 255])
            binary1 = cv2.inRange(hsv, lower_hsv, upper_hsv)
            lower_hsv = np.array([156, 43, self.config.hsv_lower_value])
            upper_hsv = np.array([180, 255, 255])
            binary2 = cv2.inRange(hsv, lower_hsv, upper_hsv)
            binary = cv2.bitwise_or(binary1, binary2)
        elif mode == 'blue':
            lower_hsv = np.array([100, 43, self.config.hsv_lower_value])
            upper_hsv = np.array([124, 255, 255])
            binary = cv2.inRange(hsv, lower_hsv, upper_hsv)
        self.mat.binary = binary
        return self.mat.binary

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
        t = (255-ret) * self.config.binary_threshold_scale + ret
        self.mat.binary = cv2.threshold(
            grayscale_mat, t, 255, cv2.THRESH_BINARY)[1]
        return self.mat.binary

    def find_contours(self, binary_mat):
        '''binary_mat -> binary_mat (lamps, contours)'''
        contours = cv2.findContours(
            binary_mat, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1]
        lamps = [Lamp(x) for x in contours]
        ################
        #  NEED UPDATE #
        ################
        max_contour_len = self.config.max_contour_len
        if len(contours) > max_contour_len:
            self.data.lamps = lamps[0:max_contour_len]
        else:
            self.data.lamps = lamps
        self.data.contours = contours
        return binary_mat

    def calc_features(self, mat):
        methods = {
            'bounding_rect': lambda x: self.calc_bounding_rects(x),
            'rotated_rect': lambda x: self.calc_rotated_rects(x),
            'contour_feature': lambda x: self.calc_contour_features(x),
            'ellipse': lambda x: self.calc_ellipses(x),
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

    def calc_contour_features(self, _mat):
        '''mat -> lamp.grayscale, lamp.point_areas, lamp.solidity'''
        if not hasattr(self.mat, 'grayscale'):
            self.split_channels(self.mat.original)
        mat = self.mat.grayscale
        lamps = self.data.lamps
        for lamp in lamps:
            x, y, w, h = lamp.bounding_rect
            roi = np.zeros_like(mat)
            cv2.drawContours(roi, [lamp.contour], -1, color=255, thickness=-1)
            roi = roi[y:y+h, x:x+w]
            pts = np.where(roi == 255)
            pts = mat[pts[0]+y, pts[1]+x]
            point_area = len(pts)
            grayscale = sum(pts) / point_area
            lamp.point_area = point_area
            lamp.grayscale = grayscale
        threshold = range(*self.config.point_area_threshold)
        self.data.lamps = [x for x in lamps if x.point_area in threshold]
        return _mat

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
    def draw_contours(self, img):
        contours = self.data.contours
        cv2.drawContours(img, contours, -1, (0, 150, 150), 2)
        return img

    def draw_bounding_rects(self, img):
        rects = self.data.bounding_rects
        for rect in rects:
            x, y, w, h = rect
            cv2.rectangle(img, (x, y), (x+w, y+h), (200, 0, 200), 2)
        return img

    def draw_rotated_rects(self, img):
        rects = self.data.rotated_rects
        for rect in rects:
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.drawContours(img, [box], 0, (0, 200, 200), 2)
        return img

    def draw_ellipses(self, img):
        ellipses = self.data.ellipses
        for ellipse in ellipses:
            cv2.ellipse(img, ellipse, (0, 255, 0), 2)
        return img

    def draw_texts(self):
        '''Usage:toolbox.draw_texts()(lambda x: x.point_area)'''
        def draw(key, img):
            lamps = self.data.lamps
            for lamp in lamps:
                x, y, w, h = lamp.bounding_rect
                cv2.putText(img, '{0:.2f}'.format(key(lamp)), (x, int(y+h+15)),
                            cv2.FONT_HERSHEY_PLAIN, 1.2, (200, 200, 200), 1
                            )
            return img
        return curry(draw)

    def draw_fps(self):
        '''Usage:toolbox.draw_fps()(fps)'''
        def draw(fps, img):
            cv2.putText(img, str(fps), (25, 50),
                        cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 200, 200), 2
                        )
            return img
        return curry(draw)

    def draw_target(self):
        '''Usage:toolbox.draw_fps()(center)'''
        def draw(center, img):
            center = (int(center[0]), int(center[1]))
            cv2.circle(img, center, 5, (50, 200, 200), -1)
            return img
        return curry(draw)

    def draw_centers(self, img, center=None):
        '''Usage:toolbox.draw_centers()'''
        lamps = self.data.lamps
        for lamp in lamps:
            x, y, w, h = lamp.bounding_rect
            cv2.circle(img, (int(x+w/2), int(y+h/2)), 5, (28, 69, 119), 3)
        if center is None:
            center = (int(img.shape[1]/2), int(img.shape[0]/2))
        else:
            center = (int(center[0]), int(center[1]))
        x, y = center
        cv2.circle(img, center, 14, (94, 148, 213), 1)
        cv2.circle(img, center, 2, (94, 148, 213), -1)
        cv2.line(img, (x-14, y), (x-18, y), (94, 148, 213), 1)
        cv2.line(img, (x+14, y), (x+18, y), (94, 148, 213), 1)
        cv2.line(img, (x, y-14), (x, y-18), (94, 148, 213), 1)
        cv2.line(img, (x, y+14), (x, y+18), (94, 148, 213), 1)
        return img

    def draw_pair_bounding_rects(self, img):
        for pair in self.data.pairs:
            rect = pair.bounding_rect
            x, y, w, h = rect
            if not hasattr(pair, 'label'):
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 200, 200), 2)
            elif pair.label == 0:
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 200, 0), 2)
            elif pair.label == 1:
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 200), 2)
        return img

    def draw_pair_bounding_text(self):
        '''Usage:toolbox.draw_pair_bounding_text()(lambda x: x.point_area)'''
        def draw(key, img):
            pairs = self.data.pairs
            for pair in pairs:
                x, y, w, h = pair.bounding_rect
                cv2.putText(img, str(key(pair)), (x, int(y+h+15)),
                            cv2.FONT_HERSHEY_PLAIN, 1.2, (200, 200, 200), 1
                            )
            return img
        return curry(draw)


if __name__ == '__main__':
    for i in range(135, 250, 1):
        img_url = 'data/test18/img{}.jpg'.format(i)
        print('Load {}'.format(img_url))
        img = helpers.load(img_url)
        config = ToolboxConfig({'target_color': 'red', 'hsv_lower_value': 100})
        toolbox = Toolbox(config)
        pipe(img,
             toolbox.start,
             helpers.peek,
             #  toolbox.split_channels,
             #  toolbox.preprocess,
             #  toolbox.binarize,
             toolbox.split_hsv,
             helpers.peek,
             toolbox.find_contours,
             toolbox.calc_features,
             toolbox.match_pairs,
             helpers.color,
             toolbox.draw_contours,
             toolbox.draw_texts()(lambda x: x.grayscale),
             helpers.showoff,
             )
        print(toolbox.data.pairs)
