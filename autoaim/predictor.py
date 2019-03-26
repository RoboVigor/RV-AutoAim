# -*- coding: utf-8 -*-
"""Predictor Module

This module tell you the truth of the lamps.

Author:
    tccoin
"""


import math
import cv2
import numpy as np
from autoaim import helpers, feature, Feature, DataLoader, pipe


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


class Predictor():
    def __init__(self, csv):
        props, w = DataLoader().read_csv(csv)
        self.props = props
        self.w = np.array(w[0])

    def predict(self, img, mode='red'):
        w = self.w
        calcdict = feature.calcdict
        # modes
        if mode == 'red':
            f = Feature(img)
        elif mode == 'blue':
            f = Feature(img, channel=lambda c: cv2.subtract(c[0], c[2]))
        elif mode == 'old':
            f = Feature(img,
                        preprocess=False,
                        channel=lambda c: c[1],
                        threshold=lambda t: (255-t)*0.5+t)
        f.calc(self.props)
        # get x_keys
        x_keys = []
        for prop in self.props:
            for x_key in calcdict.get(prop, []):
                x_keys += [x_key]
        # get x and calc y
        for lamp in f.lamps:
            x = np.array([lamp.x[k] for k in x_keys] + [1])
            lamp.y = sigmoid(x.dot(w))
            print(x)
        # debug
        pipe(
            # img.copy(),
            f.mat.copy(),
            f.draw_bounding_rects,
            f.draw_texts()(
                # lambda l: '{:.2f}'.format(l.point_area)
                lambda l: '{:.2f}'.format(l.y)
            ),
            helpers.showoff
        )


if __name__ == '__main__':
    for i in range(0, 250, 1):
        img_url = 'data/test7/img{}.jpg'.format(i)
        print('Load {}'.format(img_url))
        img = helpers.load(img_url)

        predictor = Predictor('weight.csv')
        predictor.predict(img, mode='red')
