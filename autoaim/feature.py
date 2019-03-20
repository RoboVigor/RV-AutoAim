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


class Feature():
    __default_config = {
        'channel': lambda c: cv2.subtract(c[2], c[0]),  # (b,g,r)
        'threshold': lambda t: t,
        'preprocess': False,
        'rect_area_threshold': (64, 2048),
        'point_area_threshold': (16, 2048),
    }

    def __init__(self, img, **config):
        """receive a image with rgb channel"""

        # save the original img
        self.src = img

        # update the config
        self.__config = self.__default_config.copy()
        self.__config.update(config)

        # set up the calculated values
        self.__calculated = []

        # split the channels
        channels = cv2.split(self.src)
        channel = self.__config['channel'](channels)

        # preprocess
        if self.__config['preprocess']:
            self.mat = self.apply_preprocess(channel)
        else:
            self.mat = channel

    # ===================
    # Property
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
        mat = cv2.GaussianBlur(mat, (5, 5), 0, 0, cv2.BORDER_DEFAULT)
        # mat = cv2.Sobel(mat, cv2.CV_8U, 1, 0, ksize=3)
        # _, mat = cv2.threshold(mat, 250, 255, cv2.THRESH_BINARY)
        # element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
        # element2 = cv2.getStructuringElement(cv2.MORPH_RECT, (8, 6))
        # mat = cv2.dilate(mat, element2, iterations=1)
        # mat = cv2.erode(mat, element1, iterations=1)
        # mat = cv2.dilate(mat, element2, iterations=1)
        return mat

    def apply_binarization(self, mat):
        ret = cv2.threshold(mat, 0, 255, cv2.THRESH_OTSU)[0]
        t = self.__config['threshold'](ret)
        binary_mat = cv2.threshold(mat, t, 255, cv2.THRESH_BINARY)[1]
        self.__set_calculated('binary_mat')
        return binary_mat

    # ===================
    # "calc" Function
    # mat->value
    # ===================

    def calc(self, props):
        for prop in props:
            getattr(self, prop)

    def calc_contours(self, binary_mat=None):
        '''binary_mat -> lamps, contours'''
        if binary_mat is None:
            binary_mat = self.binary_mat
        contours = cv2.findContours(
            binary_mat, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[1]
        lamps = [Lamp(x) for x in contours]
        self.__lamps = lamps
        self.__set_calculated('lamps')
        self.__set_calculated('contours')
        return lamps

    def calc_bounding_rects(self):
        '''lamp.contour -> lamp.bounding_rect, lamp.bounding_rect_area'''
        lamps = self.lamps
        for lamp in lamps:
            rect = cv2.boundingRect(lamp.contour)
            x, y, w, h = rect
            area = int(w * h)
            lamp.bounding_rect = rect
            lamp.bounding_rect_area = area
        threshold = range(*self.__config['rect_area_threshold'])
        lamps = [x for x in lamps if x.bounding_rect_area in threshold]
        self.__lamps = lamps
        self.__set_calculated('bounding_rects')
        return lamps

    def calc_rotated_rects(self):
        '''lamp.contour -> lamp.rotated_rect'''
        lamps = self.lamps
        for lamp in lamps:
            lamp.rotated_rect = cv2.minAreaRect(lamp.contour)
        self.__set_calculated('rotated_rects')
        return lamps

    def calc_greyscales_and_point_areas(self, mat=None):
        '''mat -> lamp.greyscale, lamp.point_areas
            @todo reduce the size of roi to bounding rect
        '''
        if mat is None:
            mat = self.mat.copy()
        lamps = self.lamps
        for lamp in lamps:
            roi = np.zeros_like(mat)
            cv2.drawContours(roi, [lamp.contour], -1, color=255, thickness=-1)
            pts = np.where(roi == 255)
            pts = mat[pts[0], pts[1]]
            point_area = len(pts)
            greyscale = sum(pts) / point_area
            lamp.point_area = point_area
            lamp.greyscale = greyscale
        threshold = range(*self.__config['point_area_threshold'])
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
                cv2.putText(img, str(key(lamp)),
                            (x, int(y+h+15)),
                            cv2.FONT_HERSHEY_PLAIN, 1.2, (200, 200, 200), 1
                            )
            return img
        return curry(draw)


if __name__ == '__main__':
    for i in range(1, 200, 1):
        img_url = 'data/test7/img'+str(i)+'.jpg'
        print('Load {}'.format(img_url))
        img = helpers.load(img_url)

        # for old database
        # feature = Feature(img,
        #   preprocess=False,
        #   channel=lambda c: c[1],
        #   threshold=lambda t: (255-t)*0.5+t)

        # for new database
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
            # img.copy(),
            feature.mat.copy(),
            # feature.binary_mat.copy(),
            # feature.draw_contours,
            # feature.draw_bounding_rects,
            # feature.draw_rotated_rects,
            #  feature.draw_ellipses,
            # feature.draw_texts()(lambda x: int(x.rotated_rect[2])),
            feature.draw_texts()(lambda x: int(x.bounding_rect_area)),
            helpers.showoff
        )
        print('   find {} contours'.format(len(feature.contours)))
        if exit:
            break
