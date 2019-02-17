# -*- coding: utf-8 -*-
import cv2
import numpy
import helpers


class Feature():
    def __init__(self, img):
        """receive a image with rgb channel"""
        self.__src = img  # __src should be readonly
        # split the channels
        self.src_b, self.src_g, self.src_r, = cv2.split(self.__src)
        # preprocess
        self.mat = self.preprocess(self.src_g)

    def preprocess(self, mat):
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
        if hasattr(self, '__binary_mat'):
            return self.__binary_mat
        mat = self.mat.copy()
        ret = cv2.threshold(mat, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[0]
        binary_mat = cv2.threshold(mat, (255-ret)*0.5+ret,
                                   255, cv2.THRESH_BINARY)[1]
        self.__binary_mat = binary_mat
        return binary_mat

    @property
    def areas(self):
        pass


if __name__ == '__main__':
    img = helpers.load('data/test0/img02.jpg')
    feature = Feature(img)
    helpers.showoff(feature.binary_mat)
