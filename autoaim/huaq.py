# -*- coding: utf-8 -*-
# 9/9 44/48 19/23
import cv2
import numpy as np
import math
import time

class Lamp():

    def __init__(self, contour, rect, greyscale, area, error):
        self.contour = contour
        self.greyscale = greyscale
        self.error = error
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
        elif isinstance(img,np.ndarray):
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
        mat = self.mat.copy()
        mat=cv2.GaussianBlur(mat, (3, 3), 0, 0, cv2.BORDER_DEFAULT)
        mat=cv2.medianBlur(mat, 5)
        mat = cv2.Sobel(mat, cv2.CV_8U, 1, 0, ksize = 3)
        ret3, mat = cv2.threshold(mat, 250, 255, cv2.THRESH_BINARY)
        element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
        element2 = cv2.getStructuringElement(cv2.MORPH_RECT, (8, 6))
        mat = cv2.dilate(mat, element2, iterations = 1)
        mat = cv2.erode(mat, element1, iterations = 1)
        mat = cv2.dilate(mat, element2, iterations = 1)
        if draw:
            self.draw_mat = mat
        return mat

    def threshold(self, draw=False):
        mat = self.mat.copy()
        ret = cv2.threshold(mat, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[0]
        thresh = cv2.threshold(mat, (255-ret)*0.5+ret, 255, cv2.THRESH_BINARY)[1]
        #thresh = cv2.threshold(mat, 180, 255, cv2.THRESH_BINARY)[1]
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

    def __getLampError(self, greyscale, rect):
        error = []
        # greyscale
        #print(greyscale)
        error += [max(0, (255-greyscale)/85)-1]
        # ratio
        error += [0 if rect[3]/rect[2]>1.5 else (1.5-rect[3]/rect[2])/1.5]
        #print(error)
        return error

    def findLamps(self, draw=False, contours=None, rects=None, weights=None, passline=None):
        # default parameters
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
        self.t0 = 0
        self.t1 = 0
        for i in range(0, len(contours)):
            self.t0 -= time.clock()
            rect = rects[i]
            roi = mat[rect[1]:rect[1]+rect[3],rect[0]:rect[0]+rect[2]]
            greyscale = np.mean(roi)
            self.t0 += time.clock()
            self.t1 -= time.clock()
            test_area = cv2.contourArea(contours[i])
            #mom = cv2.moments(contours[i])
            #print(mom['m00'])
            self.t1 += time.clock()
            greyscales += [greyscale]
            #areas += [len(pts)]
            areas += [test_area+1]
            #print(test_area,len(pts))
        # determine the lamp
        lamps = []
        for i in range(0, len(rects)):
            merror = np.array(self.__getLampError(greyscales[i], rects[i])).T
            mweights = np.array(weights)
            error = np.dot(merror, mweights)
            if error < passline:
                lamp = Lamp(contours[i], rects[i], greyscales[i], areas[i], error)
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
                cv2.putText(draw_mat, str(round(lamp.error,1)),
                        (lamp.x,math.floor(lamp.y+lamp.h+10)),
                        cv2.FONT_HERSHEY_COMPLEX,0.4,(200,200,200),1
                        )
        return lamps

    def __getPairError(self, this, other):
        mat = self.mat
        error = []
        # y diff
        error += [max(0,abs(this.y-other.y)/this.h-0.1)]
        # area diff
        error += [abs(this.a - other.a)/this.a]
        # greyscale
        row_begin = int((this.y+other.y)/2)
        row_stop = int((this.y+this.h+other.y+other.h)/2)
        roi_h = row_stop-row_begin
        roi_w = roi_h
        col_center = (this.x+this.w+other.x)/2
        col_begin = int(col_center-roi_w/2)
        col_stop = int(col_center+roi_w/2)
        if row_begin >= row_stop:
            return error+[1]
        if col_begin >= col_stop:
            return error+[1]
        roi = mat[row_begin:row_stop,col_begin:col_stop]
        greyscale = np.mean(roi)
        error += [max(0,(140-greyscale)/140)]
        # width/height
        ratio = (other.x+other.w-this.x)/(other.y+other.h-this.y+0.1)
        if ratio > 4.5 or ratio < 1.2:
            error += [1] # boom
        else:
            error += [0]
        return error

    def pairLamps(self, draw=False, lamps=None, weights=None, passline=None):
        # default parameters
        if weights is None:
            weights = [0.1,1,2,passline]
        if passline is None:
            passline = 2.5
        # find lamps
        if lamps is None:
            lamps = self.findLamps(draw)
        # pair the lamp
        pairs = []
        for i in range(0, len(lamps)-1):
            pair_left = lamps[i]
            is_paired = False
            error = passline
            if not pair_left.paired:
                for j in range(i+1, len(lamps)):
                    _pair_right = lamps[j]
                    # calc error
                    merror = np.array(self.__getPairError(pair_left,_pair_right)).T
                    mweights = np.array(weights)
                    _error = np.dot(merror,mweights)
                    if _error < error:
                        error = _error
                        pair_right = _pair_right
                        is_paired = True
                if is_paired:
                    pairs += [[pair_left,pair_right]]
                    pair_left.paired = True
                    pair_right.paired = True
        # delete overlapping pair
        pairs_del = []
        for i in range(0, len(pairs)-1):
            if i==len(pairs)-1:
                break
            left = pairs[i]
            for j in range(i+1, len(pairs)):
                right = pairs[j]
                if left[0].x<=right[0].x and left[1].x>=right[1].x and abs(right[0].y-left[0].y)<25:
                    pairs_del += [i]
                    break
        pairs_del.reverse()
        for i in pairs_del:
            del pairs[i]
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

    def __init__(self, img):
        super(AimMat,self).__init__(img)
        #config
        drawConfig = [False,False,True,True,True]
        areaRegion = [10,3200]
        lamp_passline = 1.5
        lamp_weights = [1,0.5]# greyscale, area
        pair_passline = 2.5
        pair_weights = [2,1,3,pair_passline] # y diff, area diff, greyscale，ratio
        #process
        thresh = self.preprocess(drawConfig[0])
        #thresh = self.threshold(drawConfig[1])
        contours,rects = self.findContours(drawConfig[2], thresh, areaRegion)
        self.lamps = self.findLamps(drawConfig[3], contours, rects, lamp_weights, lamp_passline)
        self.pairs = self.pairLamps(drawConfig[4], self.lamps, pair_weights, pair_passline)

    @property
    def areas(self):
        areas = []
        for pair in self.pairs:
            left = pair[0]
            right = pair[1]
            areas += [(right.x-left.x-left.w)*(right.y+right.h-left.y)]
        return areas

    @property
    def centers(self):
        centers = []
        for pair in self.pairs:
            left = pair[0]
            right = pair[1]
            centers += [(left.x+(right.x+right.w-left.x)/2, left.y+(right.y+right.h-left.y)/2)]
        return centers

    def __len__(self):
        return len(self.pairs)


def runTest(test_index=0):
    cv2.waitKey(0)
    tests = [
        range(1, 7),   # 0.basic
        range(1, 56), # 1.large armor in 40-56
        range(1, 38),  # 2.nightmare
        range(1, 16),  # 3.static
        range(1, 16),  # 4.drunk
        range(1, 15),  # 5.lab
        range(1, 57),  # 6.look down
        ]
    s = 0
    s0 = 0
    s1 = 0
    for i in tests[test_index]:
        str_i = '0'+str(i) if i<10 else str(i)
        #print('test'+str(test_index)+'/img'+str_i+'.jpg' )
        autoaim = AimMat('../data/test'+str(test_index)+'/img'+str_i+'.jpg')
        autoaim.showoff('miao '*3)
        s0 += autoaim.t0
        s1 += autoaim.t1
        if False:
            print('  found lamps: ',len(autoaim.lamps))
            print('  found pairs: ',len(autoaim))
            print('  areas: ',autoaim.areas)
            print('  centers: ',autoaim.centers)
        s += len(autoaim)
        if cv2.waitKey(3000) == 27:
            break
    print('Find '+str(s)+' pairs altogether.')
    print('t0:',s0)
    print('t1:',s1)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    runTest(2)