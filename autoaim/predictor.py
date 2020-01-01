# -*- coding: utf-8 -*-
"""Predictor Module

This module tell you the truth of the lamps.

Author:
    tccoin
"""


import math
import cv2
import numpy as np
from autoaim import helpers, Toolbox, ToolboxConfig, calcdict, DataLoader, pipe
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
        # config
        if mode == 'red':
            config = ToolboxConfig(
                {'target_color': 'red', 'hsv_lower_value': 100})
        elif mode == 'blue':
            config = ToolboxConfig(
                {'target_color': 'blue', 'hsv_lower_value': 100})
        toolbox = Toolbox(config)
        pipe(img,
             toolbox.start,
             toolbox.undistort,
             toolbox.split_channels,
             toolbox.preprocess,
             toolbox.binarize,
             #  toolbox.split_hsv,
             toolbox.find_contours,
             toolbox.calc_features,
             )
        toolbox.calc(self.props)
        # get x_keys
        x_keys = []
        for prop in self.props:
            for x_key in calcdict.get(prop, []):
                x_keys += [x_key]
        # get x and calc y
        for lamp in toolbox.data.lamps:
            x = np.array([lamp.x[k] for k in x_keys] + [1])
            lamp.y = sigmoid(x.dot(w_lamp))  # score
        # lamp filter
        toolbox.data.lamps = [
            l for l in toolbox.data.lamps if l.y > lamp_threshold]
        # pairs
        toolbox.match_pairs()
        for pair in toolbox.data.pairs:
            x = np.array(pair.x + [1])
            y = x.dot(np.transpose(w_pair))
            pair._y = y  # classification score
            pair.y = np.max(y)  # score
            pair.label = np.argmax(y)  # label
            anglex = np.array(pair.anglex + [1])
            angley = anglex.dot(np.transpose(w_angle))
            pair.angle = angley[0]
        # lamp filter
        toolbox.data.pairs = [l for l in toolbox.data.pairs if l.label < 2]
        # debug
        if debug:
            pipe(
                img.copy(),
                # toolbox.mat.copy(),
                # toolbox.binary_mat.copy(),
                toolbox.draw_contours,
                toolbox.draw_bounding_rects,
                # toolbox.draw_texts()(
                #     lambda l: '{:.2f}'.format(l.y)
                # ),
                toolbox.draw_pair_bounding_rects,
                toolbox.draw_pair_bounding_text()(
                    lambda l: '{:.2f}'.format(l.y)
                ),
                curry(helpers.showoff)(timeout=timeout, update=True)
            )
        return toolbox


if __name__ == '__main__':
    for i in range(135, 250, 1):
        img_url = 'data/test18/img{}.jpg'.format(i)
        print('Load {}'.format(img_url))
        img = helpers.load(img_url)
        predictor = Predictor('lamp.csv', 'pair.csv', 'angle.csv')
        predictor.predict(img, mode='red', timeout=500)
