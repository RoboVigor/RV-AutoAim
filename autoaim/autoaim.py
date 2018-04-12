# -*- coding: utf-8 -*-
import cv2
import numpy
import math


class Lamp():

    def __init__(self, contour, rect, greyscale, area):
        self.contour = contour
        self.greyscale = greyscale
        self.x = rect[0]
        self.y = rect[1]
        self.w = rect[2]
        self.h = rect[3]
        self.a = area
        self.paired = False

    def __lt__(self, other):
        return self.x < other.x

    def __eq__(self, other):
        return self.x==other.x and self.y==other.y and self.w==other.w and self.h==other.h


class ImgToolbox():

    def __init__(self, img):
        if isinstance(img, str):
            self.src = cv2.imread(img)
        else:
            self.src = img
        if len(self.src.shape) == 3:
            self.b, self.g, self.r, = cv2.split(self.src)
        self.mat = self.g
        self.drawMat = self.src.copy()

    def show(self, winname):
        cv2.imshow(winname, self.drawMat)

    def threshold(self, draw=False):
        mat = self.drawMat
        if not draw:
            mat = self.mat.copy()
        ret, thresh = cv2.threshold(mat, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        return thresh

    def findContours(self, draw=False, thresh=None):
        # threshold
        if thresh is None:
            thresh = self.threshold()
        # find contours
        all_contours = cv2.findContours(thresh, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)[1]
        # find area between 32 and 4096
        possible_contours = []
        possible_rects = []
        for i in range(0, len(all_contours)):
            contour = all_contours[i]
            x,y,w,h = cv2.boundingRect(contour)
            area = w*h
            if area>32 and area<4096:
                possible_contours.append(contour)
                possible_rects.append((x,y,w,h))
        # draw
        if draw:
            drawMat = self.drawMat
            cv2.drawContours(drawMat,possible_contours,-1,(0,0,255),3)
        return possible_contours, possible_rects

    def findLamps(self, draw=False, contours=None, rects=None):
        mat = self.mat
        # find contours
        if contours is None or rects is None:
            contours, rects = self.findContours()
        # calculate greyscale and area
        greyscales = []
        areas = []
        for i in range(0, len(contours)):
            contour = contours[i]
            cimg = numpy.zeros_like(mat)
            cv2.drawContours(cimg, [contour], -1, color=255, thickness=-1)
            pts = numpy.where(cimg == 255)
            pts = mat[pts[0], pts[1]]
            greyscale = sum(pts)/len(pts)
            greyscales.append(greyscale)
            areas.append(len(pts))
        # determine the lamp
        lamps = []
        for i in range(0, len(rects)):
            rect = rects[i]
            if greyscales[i] > 205 and rect[3]/rect[2] > 2:
                lamp = Lamp(contours[i], rects[i], greyscales[i], areas[i])
                lamps.append(lamp)
        lamps.sort()
        # draw
        if draw:
            drawMat = self.drawMat
            for i in range(0, len(lamps)):
                lamp = lamps[i]
                cv2.rectangle(drawMat,(lamp.x,lamp.y),
                        (lamp.x+lamp.w,lamp.y+lamp.h),
                        (200,200,200)
                    )
                cv2.putText(drawMat, str(math.floor(lamp.greyscale)),
                        (lamp.x,math.floor(lamp.y+lamp.h+10)),
                        cv2.FONT_HERSHEY_COMPLEX,0.4,(200,200,200),1
                        )
        return lamps

    def pairLamps(self, draw=False, lamps=None):
        # find lamps
        if lamps is None:
            lamps = self.findLamps(draw)
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
                        # score
                        _pair_score = (abs(lamp_left.y-_lamp_right.y)
                            + abs(lamp_left.a - _lamp_right.a)/lamp_left.a*5)
                        if _pair_score<pair_score:
                            pair_score = _pair_score
                            lamp_right = _lamp_right
                if not lamp_left == lamp_right:
                    pair_lamps.append([lamp_left,lamp_right])
                    lamp_left.paired = True
                    lamp_right.paired = True
        # draw
        if draw:
            drawMat = self.drawMat
            for i in range(0, len(pair_lamps)):
                pair_lamp = pair_lamps[i]
                cv2.rectangle(drawMat,(pair_lamp[0].x,pair_lamp[0].y),
                        (pair_lamp[1].x+pair_lamp[1].w,pair_lamp[1].y+pair_lamp[1].h),
                        (255,255,0)
                    )
        return pair_lamps


if __name__ == '__main__':
    '''
    for i in range(0,6):
        autoaim = ImgToolbox('../data/miao'+str(i)+'.jpg')
        autoaim.pairLamps(True)
        autoaim.show('miao'+str(i)+'.jpg')
    '''
    autoaim = ImgToolbox('../data/miao2.jpg')
    autoaim.pairLamps(True)
    autoaim.show('miao '*3)

    cv2.waitKey(0)
    cv2.destroyAllWindows()