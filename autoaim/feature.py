# -*- coding: utf-8 -*-
"""Feature Extraction Module

This module loads an image and extract the vision feature from it.

Reference:
    check https://docs.opencv.org/3.3.0/dd/d49/tutorial_py_contour_features.html

Author:
    tccoin
"""


import collections
import cv2
import numpy as np
from toolz import pipe, curry
from autoaim import helpers


class Lamp(object):
    def __init__(self, contour):
        super(Lamp, self).__setattr__('data', {'contour': contour})

    def __setattr__(self, name, value):
        self.data[name] = value

    def __getattr__(self, attr):
        try:
            return self.data[attr]
        except KeyError:
            raise AttributeError


class Pair(object):
    def __init__(self, left, right):
        super(Pair, self).__setattr__('data', {'left': left, 'right': right})

    def __setattr__(self, name, value):
        self.data[name] = value

    def __getattr__(self, attr):
        try:
            return self.data[attr]
        except KeyError:
            raise AttributeError


class Feature():

    def __init__(self, img, **config):
        """receive a image with rgb channel"""

        # save the original img
        self.src = img

        # update the config
        self.config = self.__default_config.copy()
        self.config.update(config)

        # set up the calculated values
        self.__calculated = []

        # split the channels
        channels = cv2.split(self.src)
        channel = self.config['channel'](channels)

        # preprocess
        if self.config['preprocess']:
            self.mat = self.apply_preprocess(channel)
        else:
            self.mat = channel

    # ===================
    # Property
    # Mainly for debug
    # ===================

    @property
    def binary_mat(self):
        if not self.has_calculated('binary_mat'):
            self.__binary_mat = self.apply_binarization(self.mat.copy())
        return self.__binary_mat

    @property
    def lamps(self):
        if not self.has_calculated('lamps'):
            self.calc_contours()
        return self.__lamps

    @lamps.setter
    def lamps(self, lamps):
        self.__lamps = lamps

    @property
    def contours(self):
        if not self.has_calculated('contours'):
            self.calc_contours()
        return [x.contour for x in self.__lamps]

    @property
    def bounding_rects(self):
        if not self.has_calculated('bounding_rects'):
            self.calc_bounding_rects()
        return [x.bounding_rect for x in self.__lamps]

    @property
    def rotated_rects(self):
        if not self.has_calculated('rotated_rects'):
            self.calc_rotated_rects()
        return [x.rotated_rect for x in self.__lamps]

    @property
    def ellipses(self):
        if not self.has_calculated('ellipses'):
            self.calc_ellipses()
        return [x.ellipse for x in self.__lamps]

    @property
    def greyscales(self):
        if not self.has_calculated('greyscales'):
            self.calc_greyscales_and_point_areas()
        return [x.greyscale for x in self.__lamps]

    @property
    def point_areas(self):
        if not self.has_calculated('point_areas'):
            self.calc_greyscales_and_point_areas()
        return [x.point_area for x in self.__lamps]

    @property
    def pairs(self):
        if not self.has_calculated('pairs'):
            self.calc_pairs()
        return self.__pairs

    @pairs.setter
    def pairs(self, pairs):
        self.__pairs = pairs

    # ===================
    # Helpers
    # ===================

    def has_calculated(self, prop):
        return prop in self.__calculated

    def __set_calculated(self, prop):
        self.__calculated.append(prop)

    # ===================
    # "apply" Function
    # mat->mat
    # ===================

    def apply_preprocess(self, mat):
        mat = mat.copy()
        kernel = np.ones((5, 5), np.uint8)
        mat = cv2.dilate(mat, kernel, iterations=1)
        mat = cv2.erode(mat, kernel, iterations=1)
        # cv2.imshow('Input', mat)

        return mat

    def apply_binarization(self, mat):
        if 'binary_threshold_value' in self.config:
            ret = self.config['binary_threshold_value']
        else:
            ret = cv2.threshold(mat, 0, 255, cv2.THRESH_OTSU)[0]
        t = self.config['binary_threshold_scale'](ret)
        binary_mat = cv2.threshold(mat, t, 255, cv2.THRESH_BINARY)[1]
        self.__set_calculated('binary_mat')
        return binary_mat

    # ===================
    # "calc" Function
    # mat->value
    # ===================

    def calc(self, props):
        # calc the props
        for prop in props:
            getattr(self, prop, None)
        # calc the features
        for lamp in self.lamps:
            x = {}
            for prop in props:
                for x_key in calcdict.get(prop, []):
                    func = calcdict[prop][x_key]
                    x[x_key] = func(lamp)
            lamp.x = x

    def calc_contours(self, binary_mat=None):
        '''binary_mat -> lamps, contours'''
        max_contour_len = self.config['max_contour_len']
        if binary_mat is None:
            binary_mat = self.binary_mat
        contours = cv2.findContours(
            binary_mat, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[1]
        lamps = [Lamp(x) for x in contours]
        if len(contours) > max_contour_len:
            self.__lamps = lamps[0:max_contour_len]
        else:
            self.__lamps = lamps
        self.__set_calculated('lamps')
        self.__set_calculated('contours')
        return lamps

    def calc_bounding_rects(self):
        '''lamp.contour -> lamp.bounding_rect, lamp.bounding_rect_area, lamp.bounding_rect_ratio'''
        lamps = self.lamps
        for lamp in lamps:
            rect = cv2.boundingRect(lamp.contour)
            x, y, w, h = rect
            lamp.bounding_rect = rect
            lamp.bounding_rect_area = int(w * h)
            lamp.bounding_rect_ratio = w/h
        threshold = range(*self.config['rect_area_threshold'])
        lamps = [x for x in lamps if x.bounding_rect_area in threshold]
        self.__lamps = lamps
        self.__set_calculated('bounding_rects')
        return lamps

    def calc_rotated_rects(self):
        '''lamp.contour -> lamp.rotated_rect'''
        lamps = self.lamps
        for lamp in lamps:
            rect = cv2.minAreaRect(lamp.contour)
            lamp.rotated_rect = rect
            _, (w, h), a = rect
            lamp.rotated_rect_angle = a+180 if w > h else a+90
        self.__set_calculated('rotated_rects')
        return lamps

    def calc_greyscales_and_point_areas(self, mat=None):
        '''mat -> lamp.greyscale, lamp.point_areas
            @todo reduce the size of roi to bounding rect
        '''
        if mat is None:
            mat = self.mat.copy()
        lamps = self.lamps

        self.calc(['bounding_rects'])

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
        threshold = range(*self.config['point_area_threshold'])
        lamps = [x for x in lamps if x.point_area in threshold]
        self.__lamps = lamps
        self.__set_calculated('greyscales')
        self.__set_calculated('point_areas')
        return lamps

    def calc_ellipses(self):
        '''lamp.contour -> lamp.ellipse'''
        lamps = self.lamps
        lamps = [x for x in lamps if len(x.contour) >= 6]
        for lamp in lamps:
            lamp.ellipse = cv2.fitEllipse(lamp.contour)
        self.__set_calculated('ellipses')
        return lamps

    def calc_pairs(self):
        pairs = []
        lamps = sorted(self.lamps, key=lambda x: x.bounding_rect[0])
        for i in range(len(lamps)):
            for j in range(i+1, len(lamps)):
                left = lamps[i]
                right = lamps[j]
                pair = Pair(left, right)
                (x1,y1,w1,h1),(x2,y2,w2,h2) = left.bounding_rect,right.bounding_rect
                if y1 > y2:
                    y1 = right.bounding_rect[1]
                    h1 = right.bounding_rect[3]
                    y2 = left.bounding_rect[1]
                    h2 = left.bounding_rect[3]
                pair.bounding_rect = (x1,y1,x2-x1+w2,y2-y1+h2)
                x,y,w,h = pair.bounding_rect
                if w/h > 5 or w/h < 1:
                    continue
                pair.x = [
                    (y2-y1)/200,
                    abs(w2-w1)/200,
                    abs(h2-h1)/200,
                    abs(w/h-3),
                    abs(left.rotated_rect_angle-90)/90,
                    abs(right.rotated_rect_angle-90)/90,
                    abs(left.rotated_rect_angle-right.rotated_rect_angle)/90,
                ]
                pairs += [pair]
        self.__pairs = pairs
        self.__set_calculated('pairs')
        return pairs

    # ===================
    # "draw" Function
    # ===================

    def draw_contours(self, img):
        contours = self.contours
        cv2.drawContours(img, contours, -1, (0, 0, 150), 1)
        return img

    def draw_bounding_rects(self, img):
        rects = self.bounding_rects
        for rect in rects:
            x, y, w, h = rect
            cv2.rectangle(img, (x, y), (x+w, y+h), (200, 0, 200), 2)
        return img

    def draw_rotated_rects(self, img):
        rects = self.rotated_rects
        for rect in rects:
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.drawContours(img, [box], 0, (0, 200, 200), 2)
        return img

    def draw_ellipses(self, img):
        ellipses = self.ellipses
        for ellipse in ellipses:
            cv2.ellipse(img, ellipse, (0, 255, 0), 2)
        return img

    def draw_texts(self):
        '''Usage:feature.draw_texts()(lambda x: x.point_area)'''
        def draw(key, img):
            lamps = self.lamps
            getattr(self, 'bounding_rects')
            for lamp in lamps:
                x, y, w, h = lamp.bounding_rect
                cv2.putText(img, str(key(lamp)), (x, int(y+h+15)),
                            cv2.FONT_HERSHEY_PLAIN, 1.2, (200, 200, 200), 1
                            )
            return img
        return curry(draw)

    def draw_fps(self):
        '''Usage:feature.draw_fps()(fps)'''
        def draw(fps, img):
            cv2.putText(img, str(fps), (25, 50),
                        cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 200, 200), 2
                        )
            return img
        return curry(draw)

    def draw_target(self):
        '''Usage:feature.draw_fps()(center)'''
        def draw(center, img):
            center = (int(center[0]), int(center[1]))
            cv2.circle(img, center, 5, (50, 200, 200), -1)
            return img
        return curry(draw)

    def draw_centers(self, img, center=None):
        '''Usage:feature.draw_centers()'''
        lamps = self.lamps
        getattr(self, 'bounding_rects')
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
        rects = [x.bounding_rect for x in self.pairs]
        for rect in rects:
            x, y, w, h = rect
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 200, 200), 2)
        return img

    def draw_pair_bounding_text(self):
        '''Usage:feature.draw_pair_bounding_text()(lambda x: x.point_area)'''
        def draw(key, img):
            pairs = self.pairs
            for pair in pairs:
                x, y, w, h = pair.bounding_rect
                cv2.putText(img, str(key(pair)), (x, int(y+h+15)),
                            cv2.FONT_HERSHEY_PLAIN, 1.2, (200, 200, 200), 1
                            )
            return img
        return curry(draw)

    __default_config = {
        'channel': lambda c: cv2.subtract(c[2], c[0]),  # (b,g,r)
        'binary_threshold_scale': lambda t: (255-t) * 0.1+t,
        # 'binary_threshold_value': 25,
        'preprocess': True,
        'rect_area_threshold': (32, 16384),
        'point_area_threshold': (32, 8192),
        'max_contour_len': 100
    }


calcdict = {
    'bounding_rects': {
        'bounding_rect_ratio': lambda l: l.bounding_rect_ratio
    },
    'rotated_rects': {
        'rotated_rect_angle': lambda l: abs(l.rotated_rect_angle-90)/90,
    },
    'greyscales': {
        'greyscale': lambda l: l.greyscale/255,
    },
    'point_areas': {
        'point_area': lambda l: l.point_area/2048,
    }
}

enabled_props = [
    'contours',
    'bounding_rects',
    'rotated_rects',
    'greyscales',
    'point_areas',
]


if __name__ == '__main__':
    for i in range(1, 200, 1):
        img_url = 'data/test11/img{}.jpg'.format(i)
        print('Load {}'.format(img_url))
        img = helpers.load(img_url)
        feature = Feature(img)

        feature.calc([
            'contours',
            'bounding_rects',
            'rotated_rects',
            # 'ellipses',
            'greyscales',
            'point_areas',
        ])
        exit = pipe(
            img.copy(),
            # feature.mat.copy(),
            # feature.binary_mat.copy(),
            feature.draw_contours,
            feature.draw_bounding_rects,
            # feature.draw_rotated_rects,
            #  feature.draw_ellipses,
            feature.draw_texts()(
                # lambda l: '{:.2f}'.format(l.bounding_rect_area)
                lambda l: '{:.3f}'.format(l.x['point_area'])
            ),
            helpers.showoff
        )
        print('   find {} contours'.format(len(feature.contours)))
        if exit:
            break
