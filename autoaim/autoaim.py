# -*- coding: utf-8 -*-
import cv2
import os

class Autoaim():

    def __init__(self, img):
        if isinstance(img, str):
            self.mat = cv2.imread(img)
        else:
            self.mat = img
        if len(self.mat.shape) == 3:
            self.b, self.g, self.r, = cv2.split(self.mat)

    def show(self):
        cv2.imshow('original image', self.mat)

    def threshold(self, mat=None, winname=None):
        if mat is None:
            mat = self.mat
        ret, thresh = cv2.threshold(mat, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        print('threshold: ', ret)
        if not winname is None:
            cv2.imshow(winname, thresh)
        return thresh

    def canny(self, mat=None, winname=None):
        if mat is None:
            mat = self.mat
        canny = cv2.Canny(mat, 50, 150)
        if not winname is None:
            cv2.imshow(winname, canny)
        return canny

    def getPossibleRegion(self, mat=None, winname=None):
        if mat is None:
            mat = self.mat
        thresh = self.threshold(mat)
        image,contours,hierarchy = cv2.findContours(thresh, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

        _mat = self.mat.copy()
        for i in range(0, len(contours)):
            contour = contours[i]
            x,y,w,h = cv2.boundingRect(contour)
            area = w*h
            if area>50 and area<100000:
                cv2.drawContours(_mat,[contour],-1,(0,255,0),1)
            else:
                print(area)

        if not winname is None:
            cv2.imshow(winname, _mat)
        return contours


if __name__ == '__main__':
    autoaim = Autoaim('../data/miao2.jpg')
    #autoaim.threshold(autoaim.r, 'binary')
    autoaim.getPossibleRegion(autoaim.g, 'g')
    autoaim.getPossibleRegion(autoaim.b, 'b')
    autoaim.getPossibleRegion(autoaim.r, 'r')
    cv2.waitKey(0)
    cv2.destroyAllWindows()