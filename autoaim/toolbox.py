# -*- coding: utf-8 -*-
"""Image Processing Toolbox

Author:
    tccoin
"""

import cv2
import numpy as np
from toolz import pipe, curry
from autoaim import helpers, AttrDict, Config, Lamp, Pair
import math


class Toolbox():

    def __init__(self, config=None):
        """receive a image with rgb channel"""
        if config is None:
            config = Config().data
        self.config = config
        self.mat = {}
        self.data = {}

    # ===================
    # CV
    # ===================

    def start(self, mat):
        '''mat -> mat'''
        self.mat['original'] = mat
        return self.mat['original']

    def undistort(self, mat):
        '''mat -> mat'''
        camera_matrix = np.array(self.config['camera_matrix'])
        distortion_coefficients = np.array(
            self.config['distortion_coefficients'])
        h, w = mat.shape[:2]
        new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
            camera_matrix, distortion_coefficients, (w, h), self.config['free_scaling_parameter'], (w, h))
        map1, map2 = cv2.initUndistortRectifyMap(
            camera_matrix, distortion_coefficients, None, new_camera_matrix, (w, h), cv2.CV_32FC1)
        mat = cv2.remap(mat, map1, map2, cv2.INTER_CUBIC)
        # mat = cv2.undistort(mat, camera_matrix, distortion_coefficients, None, new_camera_matrix)
        x, y, w, h = roi
        mat = mat[y:y+h, x:x+w]
        return mat

    def undistort_points(self, points):
        '''points -> points'''
        np_points = np.array([points])
        camera_matrix = np.array(self.config['camera_matrix'])
        distortion_coefficients = np.array(
            self.config['distortion_coefficients'])
        return cv2.undistortPoints(np_points, camera_matrix, distortion_coefficients).tolist()

    def split_channels(self, mat):
        '''mat -> grayscale_mat'''
        c = cv2.split(mat)
        mode = self.config['target_color']
        if mode == 'red':
            grayscale = cv2.subtract(c[2], c[0])
        elif mode == 'blue':
            grayscale = cv2.subtract(c[0], c[2])
        else:
            grayscale = c[0]
        # bgr
        self.mat['grayscale'] = grayscale
        return self.mat['grayscale']

    def split_rgb(self, mat):
        '''mat -> grayscale_mat'''
        try:
            mode = self.config['target_color']
        except:
            print('?')
        if mode == 'red':
            Lower = np.array([0, 0, 80])
            Upper = np.array([40, 40, 255])
            grayscale = cv2.inRange(mat, Lower, Upper)
        elif mode == 'blue':
            # todo
            Lower = np.array([0, 0, 80])
            Upper = np.array([40, 40, 255])
            grayscale = cv2.inRange(mat, Lower, Upper)
        else:
            # print('split_rgb() disabled for target_color "'+str(mode)+'". split_channel() is used instead.')
            grayscale = pipe(mat, self.split_channels,
                             self.preprocess, self.binarize)
        # bgr
        self.mat['grayscale'] = grayscale
        return self.mat['grayscale']

    def split_hsv(self, mat):
        '''mat -> binary_mat'''
        mode = self.config['target_color']
        hsv = cv2.cvtColor(mat, cv2.COLOR_BGR2HSV)
        if mode == 'red':
            lower_hsv = np.array([0, 43, self.config['hsv_lower_value]']])
            upper_hsv = np.array([10, 255, 255])
            binary1 = cv2.inRange(hsv, lower_hsv, upper_hsv)
            lower_hsv = np.array([156, 43, self.config['hsv_lower_value]']])
            upper_hsv = np.array([180, 255, 255])
            binary2 = cv2.inRange(hsv, lower_hsv, upper_hsv)
            binary = cv2.bitwise_or(binary1, binary2)
        elif mode == 'blue':
            lower_hsv = np.array([100, 43, self.config['hsv_lower_value]']])
            upper_hsv = np.array([124, 255, 255])
            binary = cv2.inRange(hsv, lower_hsv, upper_hsv)
        else:
            print('split_hsv() disabled for target_color "' +
                  str(mode)+'". split_channel() is used instead.')
            binary = pipe(mat, self.split_channels,
                          self.preprocess, self.binarize)
        self.mat['binary'] = binary
        return self.mat['binary']

    def preprocess(self, grayscale_mat):
        '''grayscale_mat -> grayscale_mat'''
        kernel = np.ones((5, 5), np.uint8)
        self.mat['grayscale'] = cv2.dilate(
            grayscale_mat, kernel, iterations=1)
        return self.mat['grayscale']

    def binarize(self, grayscale_mat):
        '''grayscale_mat -> binary_mat'''
        if self.config['binary_threshold_value']:
            ret = self.config['binary_threshold_value']
        else:
            ret = cv2.threshold(grayscale_mat, 0, 255, cv2.THRESH_OTSU)[0]
        t = (255-ret) * self.config['binary_threshold_scale'] + ret
        self.mat['binary'] = cv2.threshold(
            grayscale_mat, t, 255, cv2.THRESH_BINARY)[1]
        return self.mat['binary']

    def find_contours(self, binary_mat):
        '''binary_mat -> binary_mat (lamps, contours)'''
        contours = cv2.findContours(
            binary_mat, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1]
        if contours is None:
            contours = []
        lamps = [{'contour': x} for x in contours]
        ################
        #  NEED UPDATE #
        ################
        max_contour_len = self.config['max_contour_len']
        if len(contours) > max_contour_len:
            self.data['lamps'] = lamps[0: max_contour_len]
        else:
            self.data['lamps'] = lamps
        self.data['contours'] = contours
        return binary_mat

    def calc_features(self, mat):
        methods = {
            'bounding_rect': self.calc_bounding_rects,
            'rotated_rect': self.calc_rotated_rects,
            'contour_feature': self.calc_contour_features,
            'ellipse': self.calc_ellipses,
            'angle': self.calc_angle
        }
        for feature in self.config['features']:
            methods[feature](mat)
        return mat

    def calc_bounding_rects(self, mat):
        '''lamp['contour'] -> lamp['bounding_rect'], lamp['bounding_rect_area'], lamp['bounding_rect_ratio']'''
        lamps = self.data['lamps']
        for lamp in lamps:
            rect = cv2.boundingRect(lamp['contour'])
            x, y, w, h = rect
            lamp['bounding_rect'] = rect
            lamp['bounding_rect_area'] = int(w * h)
            lamp['bounding_rect_ratio'] = w/h
        threshold = self.config['rect_area_threshold']
        self.data['lamps'] = [
            x for x in lamps if self.__in(x['bounding_rect_area'], threshold)]
        return mat

    def calc_point_angle(self, point, center=None):
        x_screen, y_screen = point
        camera_matrix = np.array(self.config['camera_matrix'])
        if center is None:
            cx = camera_matrix[0, 2]
            cy = camera_matrix[1, 2]
            center = (cx, cy)
        fx = camera_matrix[0, 0]
        fy = camera_matrix[1, 1]
        yaw = math.atan((x_screen-center[0])/fx)
        pitch = math.atan((y_screen-center[1])/fy)
        return (yaw/math.pi*180, pitch/math.pi*180)

    def calc_angle(self, mat):
        '''lamp['bounding_rect'] -> lamp['angle']'''
        lamps = self.data['lamps']
        camera_matrix = np.array(self.config['camera_matrix'])
        cx = camera_matrix[0, 2]
        cy = camera_matrix[1, 2]
        fx = camera_matrix[0, 0]
        fy = camera_matrix[1, 1]
        for lamp in lamps:
            x, y, w, h = lamp['bounding_rect']
            x_screen = x+w/2
            y_screen = y+h/2
            yaw = math.atan((x_screen-cx)/fx)
            pitch = math.atan((y_screen-cy)/fy)
            lamp['angle'] = (yaw/math.pi*180, pitch/math.pi*180)
        return mat

    def calc_rotated_rects(self, mat):
        '''lamp['contour'] -> lamp['rotated_rect']'''
        lamps = self.data['lamps']
        for lamp in lamps:
            rect = cv2.minAreaRect(lamp['contour'])
            lamp['rotated_rect'] = rect
            _, (w, h), a = rect
            lamp['rotated_rect_angle'] = a+180 if w > h else a+90
        return mat

    def calc_contour_features(self, _mat):
        '''mat -> lamp['grayscale'], lamp['point_areas'], lamp['solidity']'''
        if not 'grayscale' in self.mat:
            self.split_channels(self.mat['original'])
        mat = self.mat['grayscale']
        lamps = self.data['lamps']
        for lamp in lamps:
            x, y, w, h = lamp['bounding_rect']
            roi = np.zeros_like(mat)
            cv2.drawContours(roi, [lamp['contour']], -
                             1, color=255, thickness=-1)
            roi = roi[y: y+h, x: x+w]
            pts = np.where(roi == 255)
            pts = mat[pts[0]+y, pts[1]+x]
            point_area = len(pts)
            grayscale = sum(pts) / point_area
            lamp['area'] = cv2.contourArea(lamp['contour'])
            lamp['point_area'] = point_area
            lamp['grayscale'] = grayscale
        threshold = self.config['point_area_threshold']
        self.data['lamps'] = [
            x for x in lamps if self.__in(x['area'], threshold)]
        return _mat

    def calc_ellipses(self, mat):
        '''lamp['contour'] -> lamp['ellipse']'''
        lamps = self.data['lamps']
        lamps = [x for x in lamps if len(x['contour']) >= 6]
        for lamp in lamps:
            lamp['ellipse'] = cv2.fitEllipse(lamp['contour'])
        return mat

    def match_pairs(self, mat=None):
        '''lamp -> pair'''
        pairs = []
        lamps = sorted(self.data['lamps'], key=lambda x: x['bounding_rect'][0])
        for i in range(len(lamps)):
            for j in range(i+1, len(lamps)):
                left = lamps[i]
                right = lamps[j]
                pair = {
                    'left': left,
                    'right': right
                }
                # calc bounding_rect and ratio
                lx, ly, lw, lh = left['bounding_rect']
                rx, ry, rw, rh = right['bounding_rect']
                if ly < ry:
                    pair['bounding_rect'] = (lx, ly, rx-lx+rw, ry-ly+rh)
                else:
                    pair['bounding_rect'] = (lx, ry, rx-lx+rw, ly-ry+lh)
                _, _, w, h = pair['bounding_rect']
                pair['ratio'] = w/((lh+rh)/2)
                threshold = self.config['pair_ratio_threshold']
                if self.__in(pair['ratio'], threshold):
                    pair['lx'], pair['ly'], pair['lw'], pair['lh'] = left['bounding_rect']
                    pair['rx'], pair['ry'], pair['rw'], pair['rh'] = right['bounding_rect']
                    pairs += [pair]
        self.data['pairs'] = pairs
        return mat

    # ===================
    # Helper
    # ===================

    def __in(self, value, threshold):
        return value >= threshold[0] and value <= threshold[1]

    def draw_contours(self, img):
        contours = self.data['contours']
        cv2.drawContours(img, contours, -1, (0, 150, 150), 2)
        return img

    def draw_bounding_rects(self, img):
        rects = [l['bounding_rect'] for l in self.data['lamps']]
        for rect in rects:
            x, y, w, h = rect
            cv2.rectangle(img, (x, y), (x+w, y+h), (200, 0, 200), 2)
        return img

    def draw_rotated_rects(self, img):
        rects = [l['rotated_rect'] for l in self.data['lamps']]
        for rect in rects:
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.drawContours(img, [box], 0, (0, 200, 200), 2)
        return img

    def draw_ellipses(self, img):
        ellipses = self.data['ellipses']
        for ellipse in ellipses:
            cv2.ellipse(img, ellipse, (0, 255, 0), 2)
        return img

    def put_text(self, img, text, position, font=cv2.FONT_HERSHEY_PLAIN, fontsize=1.2, thickness=1, align='left'):
        text_size = cv2.getTextSize(text, font, fontsize, thickness)[0]
        text_width = text_size[0]
        text_height = text_size[1]
        if align == 'right':
            position = (position[0]-text_width, position[1])
        elif align == 'center':
            position = (int(position[0]-text_width/2),
                        int(position[1]+text_height/2))
        cv2.putText(img, text, position, font, fontsize,
                    (200, 200, 200), thickness)
        return img

    def draw_texts(self):
        '''Usage:toolbox.draw_texts()(lambda x: x['point_area'])'''
        def draw(key, img, bias=(0, 0), fontsize=1):
            lamps = self.data['lamps']
            for lamp in lamps:
                x, y, w, h = lamp['bounding_rect']
                self.put_text(img, '{0:.2f}'.format(
                    key(lamp)), (x+bias[0], int(y+bias[1]+h+15)), fontsize=fontsize)
            return img
        return curry(draw)

    def draw_fps(self):
        '''Usage:toolbox.draw_fps()(fps)'''
        def draw(fps, img):
            cv2.putText(img, str(fps), (25, 50),
                        cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 200, 200), 2
                        )
            return img
        return curry(draw)

    def draw_target(self):
        '''Usage:toolbox.draw_target()(center)'''
        def draw(center, img):
            center = (int(center[0]), int(center[1]))
            cv2.circle(img, center, 5, (50, 200, 200), -1)
            return img
        return curry(draw)

    def draw_centers(self, img, center=None):
        '''Usage:toolbox.draw_centers()'''
        lamps = self.data['lamps']
        for lamp in lamps:
            x, y, w, h = lamp['bounding_rect']
            cv2.circle(img, (int(x+w/2), int(y+h/2)), 5, (28, 69, 119), 3)
        if center is None:
            center = (int(img.shape[1]/2), int(img.shape[0]/2))
        else:
            center = (int(center[0]), int(center[1]))
        x, y = center
        cv2.circle(img, center, 14, (94, 148, 213), 1)
        cv2.circle(img, center, 2, (94, 148, 213), -1)
        cv2.line(img, (x-14, y), (x-18, y), (94, 148, 213), 1)
        cv2.line(img, (x+14, y), (x+18, y), (94, 148, 213), 1)
        cv2.line(img, (x, y-14), (x, y-18), (94, 148, 213), 1)
        cv2.line(img, (x, y+14), (x, y+18), (94, 148, 213), 1)
        return img

    def only_that_pair(self, img):
        pairs = [p for p in self.data['pairs'] if p['y_label'] < 2]
        if len(pairs) > 0:
            pairs.sort(key=lambda x: x['y_max'])
            self.data['pairs'] = [pairs[-1]]
        return img

    def draw_pair_bounding_rects(self, img):
        for pair in self.data['pairs']:
            rect = pair['bounding_rect']
            x, y, w, h = rect
            if pair['y_label'] == 0:
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 200, 0), 2)
            elif pair['y_label'] == 1:
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 200), 2)
            # elif pair['y_label'] == 2:
            #     cv2.rectangle(img, (x, y), (x+w, y+h), (200, 200, 0), 1)
        return img

    def draw_pair_bounding_text(self):
        '''Usage:toolbox.draw_pair_bounding_text()(lambda x: x['point_area'])'''
        def draw(key, img, text_position='bottom'):
            pairs = [p for p in self.data['pairs'] if p['y_label'] < 2]
            for pair in pairs:
                text = str(key(pair))
                x, y, w, h = pair['bounding_rect']
                if text_position == 'center':
                    position = (int(x+w/2), int(y+h/2))
                elif text_position == 'bottom':
                    position = (x, int(y+h+15))
                self.put_text(img, text, position, align='center')
            return img
        return curry(draw)

    def draw_pair_index(self, img):
        '''Usage:toolbox.draw_pair_index()'''
        pairs = [p for p in self.data['pairs'] if p['y_label'] < 2]
        sorted(pairs, key=lambda p: p['y_max'], reverse=True)
        for i in range(len(pairs)):
            text = str(i)
            pair = pairs[i]
            x, y, w, h = pair['bounding_rect']
            self.put_text(img, text, (int(x+w/2), int(y+h/2)),
                          fontsize=2, thickness=3, align='center')
        return img


if __name__ == '__main__':
    for i in range(35, 100, 1):
        img_url = 'data/test19/img{}.jpg'.format(i)
        print('Load {}'.format(img_url))
        img = helpers.load(img_url)
        config = Config().data
        toolbox = Toolbox(config)
        pipe(img,
             toolbox.start,
             helpers.peek,
             # toolbox.split_channels,
             # toolbox.preprocess,
             # toolbox.binarize,
             #  toolbox.undistort,
             #  helpers.peek,
             #  toolbox.split_hsv,
             toolbox.split_rgb,
             #  helpers.peek,
             toolbox.find_contours,
             toolbox.calc_features,
             toolbox.match_pairs,
             helpers.color,
             toolbox.draw_rotated_rects,
             toolbox.draw_texts()(lambda x: x['area'], fontsize=0.8),
             helpers.showoff,
             )
        print(toolbox.data['pairs'])
