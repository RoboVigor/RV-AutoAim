# -*- coding: utf-8 -*-
import cv2
import numpy
import math

class Lamp():
    def __init__(self, contour, rect, greyscale):
        self.contour = contour
        self.greyscale = greyscale
        self.x = rect[0]
        self.y = rect[1]
        self.w = rect[2]
        self.h = rect[3]
        self.a = self.w*self.h
        self.paired = False
    def __lt__(self, other):
        return self.x < other.x
    def __eq__(self, other):
        return self.x==other.x and self.y==other.y and self.w==other.w and self.h==other.h

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
        # find area between 32 and 4096
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
            cv2.drawContours(_mat,possible_contours,-1,(0,0,255),3)
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
        # determine the lamp
        lamps = []
        for i in range(0, len(rects)):
            rect = rects[i]
            if greyscales[i] > 205 and rect[3]/rect[2] > 2:
                lamp = Lamp(contours[i], rects[i], greyscales[i])
                lamps.append(lamp)
        lamps.sort()
        # pair the lamp
        pair_lamps = []
        _lamps = lamps.copy()
        for i in range(0, len(_lamps)-1):
            lamp_left = _lamps[i]
            lamp_right = _lamps[i]
            pair_score = 10
            if not lamp_left.paired:
                for j in range(i+1, len(_lamps)):
                    _lamp_right = _lamps[j]
                    if not _lamp_right.paired:
                        _pair_score = abs(lamp_left.y-_lamp_right.y) + abs(lamp_left.a - _lamp_right.a)/lamp_left.a*7.5
                        print(abs(lamp_left.a - _lamp_right.a)/lamp_left.a)
                        if _pair_score<pair_score:
                            pair_score = _pair_score
                            lamp_right = _lamp_right
                if not lamp_left == lamp_right:
                    pair_lamps.append([lamp_left,lamp_right])
                    lamp_left.paired = True
                    lamp_right.paired = True
        # show the result
        if not winname is None:
            _mat = self.mat.copy()
            #cv2.drawContours(_mat,contours,-1,(0,0,255),2)
            for i in range(0, len(lamps)):
                lamp = lamps[i]
                cv2.putText(_mat, str(math.floor(lamp.a)),
                        (lamp.x,math.floor(lamp.y+lamp.h+10)),
                        cv2.FONT_HERSHEY_COMPLEX,0.4,(200,200,200),1
                        )
            for i in range(0, len(pair_lamps)):
                pair_lamp = pair_lamps[i]
                cv2.rectangle(_mat,(pair_lamp[0].x,pair_lamp[0].y),(pair_lamp[1].x+pair_lamp[1].w,pair_lamp[1].y+pair_lamp[1].h),(255,255,0))
            cv2.imshow(winname, _mat)



if __name__ == '__main__':
    for i in range(1,5):
        autoaim = Autoaim('../data/miao'+str(i)+'.jpg')
        autoaim.findLamp(autoaim.g, 'g'+str(i))
    autoaim = Autoaim('../data/hotel.jpg')
    autoaim.findLamp(autoaim.g, 'g'+str(i))
    cv2.waitKey(0)
    cv2.destroyAllWindows()