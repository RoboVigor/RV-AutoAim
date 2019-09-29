# -*- coding: utf-8 -*-
"""Predictor Module

This module tell you the truth of the lamps.

Author:
    tccoin
"""


import math
import cv2
import numpy as np
from autoaim import helpers, aimmat, AimMat, DataLoader, pipe
from toolz import curry


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


class Predictor():
    def __init__(self, lamp_weight, pair_weight, angle_weight):
        props, w_lamp = DataLoader().read_csv(lamp_weight)
        _, w_pair = DataLoader().read_csv(pair_weight)
        _, w_angle = DataLoader().read_csv(angle_weight)
        w_pair = np.array(w_pair).reshape(3, int(len(w_pair[0])/3))
        self.props = props
        self.w_lamp = np.array(w_lamp[0])
        self.w_pair = np.array(w_pair)
        self.w_angle = np.array(w_angle)

    def predict(self, img, mode='red', debug=True, timeout=50, lamp_threshold=0):
        w_lamp = self.w_lamp
        w_pair = self.w_pair
        w_angle = self.w_angle
        calcdict = aimmat.calcdict
        # modes
        pair_cheat_boost = 0
        if mode == 'red':
            f = AimMat(img)
        elif mode == 'blue':
            f = AimMat(img, channel=lambda c: cv2.subtract(c[0], c[2]))
        elif mode == 'white':
            f = AimMat(img, channel=lambda c: c[0])
        elif mode == 'angle':
            f = AimMat(img, channel=lambda c: c[0])
            pair_cheat_boost = 1
        elif mode == 'old':
            f = AimMat(img,
                       preprocess=False,
                       channel=lambda c: c[1],
                       binary_threshold_scale=lambda t: (255-t)*0.5+t)
        f.calc(self.props)
        # get x_keys
        x_keys = []
        for prop in self.props:
            for x_key in calcdict.get(prop, []):
                x_keys += [x_key]
        # get x and calc y
        for lamp in f.lamps:
            x = np.array([lamp.x[k] for k in x_keys] + [1])
            lamp.y = sigmoid(x.dot(w_lamp))  # score
        # lamp filter
        f.lamps = [l for l in f.lamps if l.y > lamp_threshold]
        # pairs
        f.calc_pairs()
        for pair in f.pairs:
            x = np.array(pair.x + [1])
            y = x.dot(np.transpose(w_pair))
            y[1] += pair_cheat_boost
            pair._y = y  # classification score
            pair.y = np.max(y)  # score
            pair.label = np.argmax(y)  # label
            anglex = np.array(pair.anglex + [1])
            angley = anglex.dot(np.transpose(w_angle))
            pair.angle = angley[0]
        # lamp filter
        f.pairs = [l for l in f.pairs if l.label < 2]
        # debug
        if debug:
            pipe(
                img.copy(),
                # f.mat.copy(),
                # f.binary_mat.copy(),
                f.draw_contours,
                f.draw_bounding_rects,
                # f.draw_texts()(
                #     lambda l: '{:.2f}'.format(l.y)
                # ),
                f.draw_pair_bounding_rects,
                f.draw_pair_bounding_text()(
                    lambda l: '{:.2f}'.format(l.y)
                ),
                curry(helpers.showoff)(timeout=timeout, update=True)
            )
        return f


if __name__ == '__main__':
    for i in range(705, 1000, 1):
        img_url = 'data/test_fu_1/{}.jpeg'.format(i)
        print('Load {}'.format(img_url))
        img = helpers.load(img_url)
        predictor = Predictor('weights/lamp.csv',
                              'weights/pair.csv', 'weights/angle.csv')
        predictor.predict(img, mode='blue', timeout=500)
