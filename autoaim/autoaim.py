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


class AimImageToolbox():

    def __init__(self, img):
        if isinstance(img, str):
            self.src = cv2.imread(img)
        elif isinstance(src_img,numpy.ndarray):
            self.src = img
        else:
            print('not a opencv pic, f*cker!!')
        if len(self.src.shape) == 3:
            self.src_b, self.src_g, self.src_r, = cv2.split(self.src)
        self.mat = self.src_g
        self.draw_mat = self.src.copy()

    def showoff(self, winname):
        cv2.imshow(winname, self.draw_mat)

    def preprocess(self, draw=False):
        mat = self.mat
        mat=cv2.GaussianBlur(mat, (3, 3), 0, 0, cv2.BORDER_DEFAULT)
        mat=cv2.medianBlur(mat, 5)
        mat = cv2.Sobel(mat, cv2.CV_8U, 1, 0,  ksize = 3)
        ret3, mat = cv2.threshold(mat, 250, 255, cv2.THRESH_BINARY)
        element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
        element2 = cv2.getStructuringElement(cv2.MORPH_RECT, (8, 6))
        mat = cv2.dilate(mat, element2, iterations = 1)
        mat = cv2.erode(mat, element1, iterations = 1)
        mat = cv2.dilate(mat, element2,iterations = 1)
        self.mat = mat
        if draw:
            self.draw_mat = mat
        return mat

    def threshold(self, draw=False):
        mat = self.mat.copy()
        ret = cv2.threshold(mat, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[0]
        thresh = cv2.threshold(mat, (255-ret)*0.15+ret, 255, cv2.THRESH_BINARY)[1]
        if draw:
            self.draw_mat = thresh
        return thresh

    def findContours(self, draw=False, thresh=None, area_region=None):
        #default parameter for area
        if area_region is None:
            area_region = [32,4096]
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
            if area>area_region[0] and area<area_region[1]:
                possible_contours += [contour]
                possible_rects += [(x,y,w,h)]
        # draw
        if draw:
            draw_mat = self.draw_mat
            cv2.drawContours(draw_mat,possible_contours,-1,(0,0,255), 1)
        return possible_contours, possible_rects

    def findLamps(self, draw=False, contours=None, rects=None, weights=None, passline=None):
        # default weights
        if weights is None:
            weights = [1,0.5,1]
        if passline is None:
            passline = 1.5
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
            greyscales += [greyscale]
            areas += [len(pts)]
        # fit ellipse
        ellipses = []
        for i in range(0, len(contours)):
            contour = contours[i]
            if len(contour)<6:
                contour = contours[i-1]
            ellipse = cv2.fitEllipse(contour)
            ellipses += [ellipse]
        # determine the lamp
        lamps = []
        for i in range(0, len(rects)):
            rect = rects[i]
            score1 = (255-greyscales[i])/35
            score1 = 0 if score1<0 else score1
            score2 = 0 if rect[3]/rect[2]>1.5 else (1.5-rect[3]/rect[2])/1.5
            angle = ellipses[i][2]
            score3 = (0 if angle<15 else (angle-15)/75) if angle<90 else (0 if angle>165 else (165-angle)/75)
            score = score1*weights[0] + score2*weights[1]+ score3*weights[2]
            if score < passline:
                lamp = Lamp(contours[i], rects[i], ellipses[i], greyscales[i], areas[i], score)
                lamps += [lamp]
        lamps.sort()
        # draw
        if draw:
            draw_mat = self.draw_mat
            for i in range(0, len(lamps)):
                lamp = lamps[i]
                cv2.rectangle(draw_mat,(lamp.x,lamp.y),
                        (lamp.x+lamp.w,lamp.y+lamp.h),
                        (200,200,200)
                    )
                cv2.putText(draw_mat, str(round(lamp.score,1)),
                        (lamp.x,math.floor(lamp.y+lamp.h+10)),
                        cv2.FONT_HERSHEY_COMPLEX,0.4,(200,200,200),1
                        )
        return lamps

    def pairLamps(self, draw=False, lamps=None, weights=None):
        # default weights
        if weights is None:
            weights = [1,5]
        # find lamps
        if lamps is None:
            lamps = self.findLamps(draw)
        # pair the lamp
        pairs = []
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
                        score1 = abs(lamp_left.y-_lamp_right.y)
                        score2 = abs(lamp_left.a - _lamp_right.a)/lamp_left.a
                        _pair_score = score1*weights[0]+ score2*weights[1]
                        if _pair_score<pair_score:
                            pair_score = _pair_score
                            lamp_right = _lamp_right
                if not lamp_left == lamp_right:
                    pairs += [[lamp_left,lamp_right]]
                    lamp_left.paired = True
                    lamp_right.paired = True
        # delete overlapping pair
        for i in range(0, len(pairs)-1):
            if i==len(pairs)-1:
                break
            left = pairs[i]
            for j in range(i+1, len(pairs)):
                right = pairs[j]
                if left[1].x+left[1].w>right[1].x+right[1].w and right[0].y-left[0].y<25:
                    del pairs[i]
                    i = i-1
                    break
        # delete lights above
        del_pairs = []
        for i in range(0, len(pairs)):
            pair = pairs[i]
            if pair[0].y/480<0.35:
                del_pairs += [i]
        for i in range(0, len(del_pairs)):
            print(del_pairs[len(del_pairs)-1-i], len(pairs))
            del pairs[del_pairs[len(del_pairs)-1-i]]
        # draw
        if draw:
            draw_mat = self.draw_mat
            for i in range(0, len(pairs)):
                pair = pairs[i]
                left_lamp = pair[0]
                right_lamp = pair[1]
                cv2.rectangle(draw_mat,(left_lamp.x,left_lamp.y),
                        (right_lamp.x+right_lamp.w,right_lamp.y+right_lamp.h),
                        (255,255,0)
                    )
        return pairs


class AimMat(AimImageToolbox):
    def __init__(self, img, drawConfig=None, areaRegion=None, lamp_weights=None, lamp_passline=None, pair_weights=None):
        super(AimMat,self).__init__(img)
        if drawConfig is None or not len(drawConfig) == 5:
            drawConfig = [False,False,False,False,True]
        #self.preprocess(drawConfig[0])
        thresh = self.threshold(drawConfig[1])
        contours,rects = self.findContours(drawConfig[2], thresh, areaRegion)
        lamps = self.findLamps(drawConfig[3], contours, rects, lamp_weights, lamp_passline)
        pairs = self.pairLamps(drawConfig[4], lamps, pair_weights)
        self.len = len(pairs)


def runTest(test_index=0):
    tests = [
        range(1, 7),
        range(1, 56),
        range(1, 38),
        range(1, 16),
        range(1, 16),
        ]
    s = 0
    for i in tests[test_index]:
        str_i = '0'+str(i) if i<10 else str(i)
        print('test'+str(test_index)+'/img'+str_i+'.jpg' )
        autoaim = AimMat('../data/test'+str(test_index)+'/img'+str_i+'.jpg')
        autoaim.showoff('miao '*3)
        s += autoaim.len
        if cv2.waitKey(0) & 0xFF == 27:
            break
    print('> Find '+str(s)+' pairs.')
    cv2.destroyAllWindows()


if __name__ == '__main__':
    runTest(2)