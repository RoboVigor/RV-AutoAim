# -*- coding: utf-8 -*-
import cv2
import numpy
import math

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

    def findPossibleContours(self, mat=None, winname=None):
        if mat is None:
            mat = self.g
        # binarize
        src = self.threshold(mat)
        # find contours
        all_contours = cv2.findContours(src, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)[1] #get the contour
        # find area between 50 and 50000
        possible_contours = []
        possible_rects = []
        for i in range(0, len(all_contours)):
            contour = all_contours[i]
            x,y,w,h = cv2.boundingRect(contour)
            area = w*h
            if area >32 and area < 4096:
                possible_contours.append(contour)
                possible_rects.append((x,y,w,h))
        # draw the contours
        if not winname is None:
            _mat = self.mat.copy()
            #cv2.drawContours(_mat,all_contours,-1,(0,255,0),1)
            cv2.drawContours(_mat,possible_contours,-1,(0,0,255),1)
            cv2.imshow(winname, _mat)
            print('find '+str(len(possible_contours))+' possible contours.')
        return possible_contours, possible_rects

    def findLamp(self, mat=None, winname=None):
        if mat is None:
            mat = self.g
        # find contours
        contours, rects = self.findPossibleContours(mat)
        # calculate greyscale value for every contour
        greyscales = []
        for i in range(0, len(contours)):
            contour = contours[i]
            cimg = numpy.zeros_like(mat)
            cv2.drawContours(cimg, [contour], -1, color=255, thickness=-1)
            pts = numpy.where(cimg == 255)
            pts = mat[pts[0], pts[1]]
            greyscale = sum(pts)/len(pts)
            greyscales.append(greyscale)
        # show the result
        if not winname is None:
            _mat = self.mat.copy()
            cv2.drawContours(_mat,contours,-1,(0,0,255),1)
            for i in range(0, len(rects)):
                if greyscales[i]>200:
                    rect = rects[i]
                    cv2.putText(_mat,str(math.floor(greyscales[i])),
                            (rect[0],math.floor(rect[1]+rect[3]*1+10)),
                            cv2.FONT_HERSHEY_COMPLEX,0.4,(200,200,200),1)
            cv2.imshow(winname, _mat)
        print(greyscales)



if __name__ == '__main__':
    autoaim = Autoaim('../data/miao2.jpg')
    #autoaim.findPossibleContours(autoaim.g, 'g')
    autoaim.findLamp(autoaim.g, 'g')
    cv2.waitKey(0)
    cv2.destroyAllWindows()