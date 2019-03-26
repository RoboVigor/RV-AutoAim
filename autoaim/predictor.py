# -*- coding: utf-8 -*-
"""Predictor Module

This module tell you the truth of the lamps.

Author:
    tccoin
"""


import math
import cv2
import numpy as np
from autoaim import helpers, Feature, DataLoader, pipe


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


class Predictor():
    def __init__(self, csv):
        props, w = DataLoader().read_csv(csv)
        self.props = props
        self.w = np.array(w[0])

    def predict(self, img, mode='red'):
        w = self.w
        if mode == 'red':
            feature = Feature(img)
        elif mode == 'blue':
            feature = Feature(img, channel=lambda c: cv2.subtract(c[0], c[2]))
        elif mode == 'old':
            feature = Feature(img,
                              preprocess=False,
                              channel=lambda c: c[1],
                              threshold=lambda t: (255-t)*0.5+t)
        feature.calc(self.props)
        for lamp in feature.lamps:
            x = np.array([x for x in lamp.x.values()] + [1])
            lamp.y = sigmoid(x.dot(w))
        pipe(
            # img.copy(),
            feature.mat.copy(),
            feature.draw_bounding_rects,
            feature.draw_texts()(
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
