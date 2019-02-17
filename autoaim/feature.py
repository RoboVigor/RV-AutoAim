# -*- coding: utf-8 -*-
# reference: check https://docs.opencv.org/3.3.0/dd/d49/tutorial_py_contour_features.html

import cv2
import numpy as np
from . import helpers


class Feature():
    __default_config = {
        # input
        'preferred_channel': 1,  # (b,g,r)
        'preprocess': True,
        # filter
        'rect_area_threshold': (32, 4096),
        # weight
        # debug
        'debug_contours': True
    }

    def __init__(self, img, **config):
        """receive a image with rgb channel"""
        self.__src = img
        self.__config = self.__default_config.copy()
        self.__config.update(config)

        # split the channels
        channels = cv2.split(self.__src)
        preferred_channel = channels[self.__config['preferred_channel']]

        # preprocess
        if self.__config['preferred_channel']:
            self.mat = self.__preprocess(preferred_channel)
        else:
            self.mat = preferred_channel

        # debug
        self.debug_mat = self.mat.copy()

    def __preprocess(self, mat):
        mat = mat.copy()
        mat = cv2.GaussianBlur(mat, (3, 3), 0, 0, cv2.BORDER_DEFAULT)
        mat = cv2.medianBlur(mat, 5)
        mat = cv2.Sobel(mat, cv2.CV_8U, 1, 0, ksize=3)
        _, mat = cv2.threshold(mat, 250, 255, cv2.THRESH_BINARY)
        element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
        element2 = cv2.getStructuringElement(cv2.MORPH_RECT, (8, 6))
        mat = cv2.dilate(mat, element2, iterations=1)
        mat = cv2.erode(mat, element1, iterations=1)
        mat = cv2.dilate(mat, element2, iterations=1)
        return mat

    @property
    def binary_mat(self):
        if not hasattr(self, '__binary_mat'):
            self.__calc_binary_mat()
        return self.__binary_mat

    def __calc_binary_mat(self):
        mat = self.mat.copy()
        ret = cv2.threshold(mat, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[0]
        binary_mat = cv2.threshold(mat, (255-ret)*0.5+ret,
                                   255, cv2.THRESH_BINARY)[1]
        self.__binary_mat = binary_mat

    @property
    def contours(self):
        if not hasattr(self, '__contours'):
            self.__calc_contours()
        return self.__contours

    @property
    def rects(self):
        if not hasattr(self, '__rects'):
            self.__calc_contours()
        return self.__rects

    @property
    def rect_areas(self):
        if not hasattr(self, '__rect_areas'):
            self.__calc_contours()
        return self.__rect_areas

    def __calc_contours(self):
        '''
        @todo add a method to calc contours
        @todo replace boundingRect with minAreaRect
        '''
        rect_area_threshold = self.__config['rect_area_threshold']
        binary_mat = self.binary_mat
        # find contours
        all_contours = cv2.findContours(
            binary_mat, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[1]
        # filter contours
        contours = []
        rects = []
        rect_areas = []
        for contour in all_contours:
            rect = cv2.boundingRect(contour)
            x, y, w, h = rect
            rect_area = w * h
            if rect_area > rect_area_threshold[0] and rect_area < rect_area_threshold[1]:
                contours.append(contour)
                rects.append(rect)
                rect_areas.append(rect_area)
        # debug
        if self.__config['debug_contours']:
            debug_mat = self.debug_mat
            cv2.drawContours(debug_mat, all_contours, -1, (0, 0, 150), 1)
            cv2.drawContours(debug_mat, contours, -1, (0, 0, 255), 2)
        # save
        self.__contours = contours
        self.__rects = rects
        self.__rect_areas = rect_areas

    @property
    def greyscales(self):
        if not hasattr(self, '__greyscales'):
            self.__calc_greyscales_and_point_areas()
        return self.__greyscales

    @property
    def point_areas(self):
        if not hasattr(self, '__point_areas'):
            self.__calc_greyscales_and_point_areas()
        return self.__point_areas

    def __calc_greyscales_and_point_areas(self):
        mat = self.mat
        contours = self.contours
        # calc
        greyscales = []
        point_areas = []
        for contour in contours:
            roi = np.zeros_like(mat)
            cv2.drawContours(roi, [contour], -1, color=255, thickness=-1)
            pts = np.where(roi == 255)
            pts = mat[pts[0], pts[1]]
            point_area = len(pts)
            greyscale = sum(pts) / point_area
            greyscales.append(greyscale)
            point_areas.append(point_area)
        # save
        self.__greyscales = greyscales
        self.__point_areas = point_areas

    @property
    def ellipses(self):
        if not hasattr(self, '__ellipses'):
            self.__calc_ellipses()
        return self.__ellipses

    def __calc_ellipses(self):
        contours = self.contours
        # calc
        ellipses = []
        for contour in contours:
            if len(contour) < 6:
                ellipse = None
            else:
                ellipse = cv2.fitEllipse(contour)
            ellipses += [ellipse]
        # save
        self.__ellipses = ellipses


if __name__ == '__main__':
    img = helpers.load('data/test0/img02.jpg')
    feature = Feature(img)
    print(feature.rect_areas)
    print(feature.greyscales)
    print(feature.ellipses)
    helpers.showoff(feature.binary_mat)
