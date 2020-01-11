# -*- coding: utf-8 -*-
"""Predictor Module

This module tell you the truth of the lamps.

Author:
    tccoin
"""


import math
import cv2
import numpy as np
from autoaim import helpers, Toolbox, Config, DataLoader, pipe
from toolz import curry


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


class Predictor():
    def __init__(self, config=Config()):
        self.config = config
        self.toolbox = Toolbox(config)
        #####
        props, w_lamp = DataLoader().read_csv(config.lamp_weight)
        _, w_pair = DataLoader().read_csv(config.pair_weight)
        w_pair = np.array(w_pair).reshape(3, int(len(w_pair[0])/3))
        self.props = props
        self.w_lamp = np.array(w_lamp[0])
        self.w_pair = np.array(w_pair)

    def gather_lamp_features(self, img):
        features_map = {
            'bounding_rect': [('aspect_ratio', lambda l: l.bounding_rect_ratio)],
            'rotated_rect': [('rotated_angle', lambda l: abs(l.rotated_rect_angle-90)/90)],
            'contour_feature': [('grayscale', lambda l: l.grayscale/255)],
            'ellipse': [],
            'angle': [('point_areas', lambda l: l.point_area/2048)]
        }
        pipe(img,
             self.toolbox.start,
             #  self.toolbox.undistort,
             self.toolbox.split_hsv,
             self.toolbox.find_contours,
             self.toolbox.calc_features,
             )
        lamps = self.toolbox.data.lamps
        x_header = []
        x = []
        for feature in self.config.features:
            for map in features_map[feature]:
                x_header += [map[0]]
                x += [[map[1](l) for l in lamps]]
        x = np.array(x).T
        self.x_header = x_header
        self.x_lamp = x
        return x

    def gather_pair_features(self):
        self.toolbox.match_pairs()
        pairs = self.toolbox.data.pairs
        x = []
        new_pairs = []
        for pair in pairs:
            left, right = (pair.left, pair.right)
            x1, y1, w1, h1 = left.bounding_rect
            x2, y2, w2, h2 = right.bounding_rect
            if y1 > y2:
                y1 = right.bounding_rect[1]
                h1 = right.bounding_rect[3]
                y2 = left.bounding_rect[1]
                h2 = left.bounding_rect[3]
            pair.bounding_rect = (x1, y1, x2-x1+w2, y2-y1+h2)
            _, _, w, h = pair.bounding_rect
            if w/h > 8 or w/h < 2:
                continue
            pair.ratio = w/((h1+h2)/2)
            pair.x = [
                abs(pair.ratio-3.17),
                abs(pair.ratio-6.2),
                abs(y2-y1)/200,
                abs(w2-w1)/200,
                abs(h2-h1)/200,
                abs(left.rotated_rect_angle-90)/90,
                abs(right.rotated_rect_angle-90)/90,
                abs(left.rotated_rect_angle-right.rotated_rect_angle)/90
            ]
            new_pairs += [pair]
            x += [pair.x]
        self.toolbox.data.pairs = new_pairs
        return np.array(x)

    def predict(self, img, debug=True, timeout=50):
        # lamp
        x_lamp = self.gather_lamp_features(img)
        ones = np.ones((x_lamp.shape[0], 1))
        x_lamp = np.concatenate((x_lamp, ones), axis=1)
        y_lamp = x_lamp.dot(self.w_lamp.T)
        data = self.toolbox.data
        lamp_threshold = self.config.lamp_threshold
        for i in range(len(y_lamp)):
            data.lamps[i].y = y_lamp[i]
        data.lamps = [l for l in data.lamps if l.y > lamp_threshold]
        # pair
        x_pair = self.gather_pair_features()
        ones = np.ones((x_pair.shape[0], 1))
        x_pair = np.concatenate((x_pair, ones), axis=1)
        y_pair = x_pair.dot(self.w_pair.T)
        for i in range(len(y_pair)):
            pair = data.pairs[i]
            pair.y = y_pair[i]
            pair.ymax = np.max(y_pair[i])
            pair.label = np.argmax(y_pair[i])
        # debug
        if debug:
            pipe(
                img.copy(),
                self.toolbox.draw_contours,
                self.toolbox.draw_bounding_rects,
                # toolbox.draw_texts()(
                #     lambda l: '{:.2f}'.format(l.y)
                # ),
                self.toolbox.draw_pair_bounding_rects,
                self.toolbox.draw_pair_bounding_text()(
                    lambda p: '{:.2f}'.format(p.ymax)
                ),
                curry(helpers.showoff)(timeout=timeout, update=True)
            )
        # will change in the future
        return self.toolbox


if __name__ == '__main__':
    for i in range(0, 100, 1):
        img_url = 'data/test18/img{}.jpg'.format(i)
        print('Load {}'.format(img_url))
        img = helpers.load(img_url)
        predictor = Predictor()
        predictor.predict(img, debug=True, timeout=500)
