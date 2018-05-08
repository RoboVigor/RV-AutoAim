# -*- coding: utf-8 -*-
# 9/9 34/48 15/23
import cv2
import numpy as np
import math

class Lamp():

    def __init__(self, contour, rect, ellipse, greyscale, area, error):
        self.contour = contour
        self.greyscale = greyscale
        self.ellipse = ellipse
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
        print((255-ret)*0.5+ret)
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

    def __getLampError(self, greyscale, rect, ellipse):
        error = []
        # greyscale
        error += [max(0, (255-greyscale)/35)]
        # ratio
        error += [0 if rect[3]/rect[2]>1.5 else (1.5-rect[3]/rect[2])/1.5]
        # ellipse
        if ellipse is None:
            error += [0.5]
        else:
            angle = ellipse[2]
            error += [(0 if angle<15 else (angle-15)/75)
                if angle<90 else
                (0 if angle>165 else (165-angle)/75)]
        #print('-----')
        #print('greyscale:',greyscale)
        #print('ratio:',rect[3]/rect[2])
        #print('error:',error)
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
        for i in range(0, len(contours)):
            contour = contours[i]
            ROI = np.zeros_like(mat)
            cv2.drawContours(ROI, [contour], -1, color=255, thickness=-1)
            pts = np.where(ROI == 255)
            pts = mat[pts[0], pts[1]]
            greyscale = sum(pts)/len(pts)
            greyscales += [greyscale]
            areas += [len(pts)]
        # fit ellipse
        ellipses = []
        for i in range(0, len(contours)):
            contour = contours[i]
            if len(contour)<6:
                ellipse = None
            else:
                ellipse = cv2.fitEllipse(contour)
            ellipses += [ellipse]
        # determine the lamp
        lamps = []
        for i in range(0, len(rects)):
            merror = np.array(self.__getLampError(greyscales[i], rects[i], ellipses[i])).T
            mweights = np.array(weights)
            error = np.dot(merror, mweights)
            if error < passline:
                lamp = Lamp(contours[i], rects[i], ellipses[i], greyscales[i], areas[i], error)
                lamps += [lamp]#lamps.append(lamp)
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
        error += [abs(this.y-other.y)]
        # area diff
        error += [abs(this.a - other.a)/this.a]
        # greyscale
        col_begin = this.x+this.w
        col_stop = other.x
        ROI_w = col_stop - col_begin
        ROI_h = ROI_w
        row_center = this.y+math.floor((other.y+other.h-this.y)/2)
        row_begin = math.floor(row_center-ROI_h/2)
        row_stop = math.floor(row_center+ROI_h/2)
        if row_begin >= row_stop:
            return error+[1]
        if col_begin >= col_stop:
            return error+[1]
        ROI = mat[row_begin:row_stop,col_begin:col_stop]
        ROI_thresh = cv2.threshold(ROI, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
        pts = np.where(ROI_thresh == 255)
        if not len(pts) == 2:
            return error+[1]
        error += [1-len(mat[pts[0],pts[1]])/ROI_w/ROI_w]
        # width/height
        ratio = (other.x+other.w-this.x)/(other.y+other.h-this.y+0.1)
        if ratio > 4.5 or ratio < 1.2:
            error[2] = 1
        return error

    def pairLamps(self, draw=False, lamps=None, weights=None, passline=None):
        # default parameters
        if weights is None:
            weights = [0.1,1,2]
        if passline is None:
            passline = 2.5
        # find lamps
        if lamps is None:
            lamps = self.findLamps(draw)
        # pair the lamp
        pairs = []
        for i in range(0, len(lamps)-1):
            pair_left = lamps[i]
            pair_right = lamps[i]
            error = passline
            if not pair_left.paired:
                for j in range(i+1, len(lamps)):
                    _pair_right = lamps[j]
                    if not _pair_right.paired:
                        # calc error
                        merror = np.array(self.__getPairError(pair_left,_pair_right)).T
                        mweights = np.array(weights)
                        _error = np.dot(merror,mweights)
                        if _error < error:
                            error = _error
                            pair_right = _pair_right
                if not pair_left == pair_right:
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
                if left[1].x+left[1].w>right[1].x+right[1].w and right[0].y-left[0].y<25:
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
        drawConfig = [True,False,False,True,True]
        areaRegion = [32,3200]
        lamp_weights = [1,0.5,1]# greyscale, area, ellipse
        lamp_passline = 1.5
        pair_weights = [0.1,1,2] # y diff, area diff, greyscale
        pair_passline = 2
        #process
        #thresh = self.preprocess(drawConfig[0])
        thresh = self.threshold(drawConfig[1])
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
    tests = [
        range(1, 7),   # 0.basic
        range(40, 56), # 1.large armor in 40-56
        range(1, 38),  # 2.nightmare
        range(1, 16),  # 3.static
        range(1, 16),  # 4.drunk
        range(1, 15),  # 5.lab
        range(1, 57),  # 6.look down
        ]
    s = 0
    for i in tests[test_index]:
        str_i = '0'+str(i) if i<10 else str(i)
        print('test'+str(test_index)+'/img'+str_i+'.jpg' )
        autoaim = AimMat('../data/test'+str(test_index)+'/img'+str_i+'.jpg')
        autoaim.showoff('miao '*3)
        print('  found lamps: ',len(autoaim.lamps))
        print('  found pairs: ',len(autoaim))
        print('  areas: ',autoaim.areas)
        print('  centers: ',autoaim.centers)
        s += len(autoaim)
        if cv2.waitKey(0) == 27:
            break
    print('Find '+str(s)+' pairs altogether.')
    cv2.destroyAllWindows()


if __name__ == '__main__':
    runTest(0)