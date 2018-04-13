# -*- coding: utf-8 -*-
import cv2
import numpy
import math


class Lamp():

    def __init__(self, contour, rect, ellipse, greyscale, area, score=0):
        self.contour = contour
        self.greyscale = greyscale
        self.ellipse = ellipse
        self.score = score
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
        mat = self.mat.copy()
        ret = cv2.threshold(mat, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[0]
        thresh = cv2.threshold(mat, (255-ret)*0.15+ret, 255, cv2.THRESH_BINARY)[1]
        if draw:
            self.drawMat = thresh
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
            cv2.drawContours(drawMat,possible_contours,-1,(0,0,255), 1)
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
        # fit ellipse
        ellipses = []
        for i in range(0, len(contours)):
            contour = contours[i]
            if len(contour)<6:
                contour = contours[i-1]
            ellipse = cv2.fitEllipse(contour)
            ellipses.append(ellipse)
        # determine the lamp
        lamps = []
        for i in range(0, len(rects)):
            rect = rects[i]
            # greyscales[i] > 205 and rect[3]/rect[2] > 2
            score1 = (255-greyscales[i])/35
            score1 = 0 if score1<0 else score1
            score2 = 0 if rect[3]/rect[2]>1.5 else (1.5-rect[3]/rect[2])/1.5
            angle = ellipses[i][2]
            score3 = (0 if angle<15 else (angle-15)/75) if angle<90 else (0 if angle>165 else (165-angle)/75)
            score = score1 + score2/2 + score3
            #print(round(score1,2),round(score2,2),round(score3,2))
            #greyscales[i]>205 and rect[3]/rect[2] > 1 and (ellipses[i][2]<20 or ellipses[i][2]>170)
            if score<1.5:
                lamp = Lamp(contours[i], rects[i], ellipses[i], greyscales[i], areas[i], score)
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
                cv2.putText(drawMat, str(round(lamp.score,1)),
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
        # pair score
        for i in range(0, len(lamps)-1):
            lamp_left = lamps[i]
            lamp_right = lamps[i]
            pair_score = 10
            if not lamp_left.paired:
                for j in range(i+1, len(lamps)):
                    _lamp_right = lamps[j]
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
        # delete overlapping pair
        for i in range(0, len(pair_lamps)-1):
            if i==len(pair_lamps)-1:
                break
            left = pair_lamps[i]
            for j in range(i+1, len(pair_lamps)):
                right = pair_lamps[j]
                if left[1].x+left[1].w>right[1].x+right[1].w and right[0].y-left[0].y<25:
                    del pair_lamps[i]
                    i = i-1
                    break
        # delete lights above
        for i in range(0, len(pair_lamps)):
            if i==len(pair_lamps):
                break
            pair_lamp = pair_lamps[i]
            if pair_lamp[0].y/480<0.35:
                del pair_lamps[i]
                i = i-1
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
    #213,268
    test_index = 1
    tests = [
        range(1, 7),
        range(1, 56),
        range(1, 38),
        range(1, 16),
        range(1, 16),
        ]
    for i in tests[test_index]:
        str_i = '0'+str(i) if i<10 else str(i)
        print('../data/test'+str(test_index)+'/img'+str_i+'.jpg' )
        autoaim = ImgToolbox('../data/test'+str(test_index)+'/img'+str_i+'.jpg')
        '''autoaim.threshold(True)
        autoaim.findContours(True)
        autoaim.findLamps(True)'''
        autoaim.pairLamps(True)
        #autoaim.show('miao '*3)
        #cv2.waitKey(0)
    '''
    autoaim = ImgToolbox('../data/miao2.jpg')
    autoaim.pairLamps(True)
    autoaim.show('miao '*3)
    '''

    #cv2.waitKey(0)
    cv2.destroyAllWindows()