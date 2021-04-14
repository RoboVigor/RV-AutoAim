# -*- coding: utf-8 -*-
"""Predictor Module

This module tell you the truth of the lamps.

Author:
    tccoin
"""


import math
import cv2
import numpy as np
from autoaim import helpers, Toolbox, Config
from toolz import curry, pipe


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


class Predictor():
    def __init__(self, config=None, verify_weights=True):
        # config
        if config is None:
            config = Config()
        self.config = config
        self.toolbox = Toolbox(config)
        # features
        self.features_map_lamp = {
            'contour_feature': [
                ('grayscale', lambda l: l['grayscale']/255),
                ('point_areas', lambda l: l['area']/2048)
            ],
            'bounding_rect': [
                ('aspect_ratio', lambda l: l['bounding_rect_ratio'])
            ],
            'rotated_rect': [
                ('rotated_angle', lambda l: abs(l['rotated_rect_angle']-90)/90)
            ],
            'ellipse': []
        }
        self.features_map_pair = {
            'contour_feature': [
                ('ratio_small', lambda p: abs(p['ratio']-3.17)),
                ('ratio_large', lambda p: abs(p['ratio']-6.2))
            ],
            'bounding_rect': [
                ('y_diff', lambda p: abs(p['ly']-p['ry'])/200),
                ('width_diff', lambda p: abs(p['lw']-p['rw'])/200),
                ('height_diff', lambda p: abs(p['lh']-p['rh'])/200)
            ],
            'rotated_rect': [
                ('rotated_angle_left', lambda p: abs(
                    p['left']['rotated_rect_angle']-90)/90),
                ('rotated_angle_right', lambda p: abs(
                    p['right']['rotated_rect_angle']-90)/90),
                ('rotated_angle_diff', lambda p: abs(
                    p['left']['rotated_rect_angle']-p['right']['rotated_rect_angle'])/90)
            ]
        }

        # read header and weights
        try:
            self.header_lamp, w_lamp = helpers.read_csv(config['lamp_weight'])
            self.header_pair, w_pair = helpers.read_csv(config['pair_weight'])
            self.w_lamp = np.array(w_lamp[0])
            self.w_pair = np.array(w_pair)

            # verify weights
            if verify_weights:
                verified = self.verify_header(
                    self.header_lamp, self.features_map_lamp)
                if not verified:
                    print('!!! Lamp weights NOT verified.')
                verified = self.verify_header(
                    self.header_pair, self.features_map_pair)
                if not verified:
                    print('!!! Pair weights NOT verified.')
        except(ValueError):
            print('!!! Error when loading weights')
            raise ValueError
        except(FileNotFoundError):
            print('!!! Weights not found: ' + config['lamp_weight'])
            raise FileNotFoundError

    def verify_header(self, header_model, features_map):
        header_config = self.generate_header(features_map)
        return header_model == header_config

    def generate_header(self, features_map):
        header = []
        for feature in self.config['features']:
            for map in features_map.get(feature, []):
                header += [feature+'.'+map[0]]
        return header

    def resolve_features(self, features_map, data):
        x = []
        for feature in self.config['features']:
            for map in features_map.get(feature, []):
                x += [[map[1](d) for d in data]]
        return np.array(x).T

    def calculate_lamps(self, img):
        toolbox = self.toolbox
        pipe(img,
             toolbox.start,
             #  toolbox.undistort,
             #  toolbox.split_channels,
             #  toolbox.preprocess,
             #  toolbox.binarize,
             #  toolbox.split_hsv,
             toolbox.split_rgb,
             toolbox.find_contours,
             toolbox.calc_features,
             )

    def predict(self, img, debug=False, timeout=50):
        self.calculate_lamps(img)
        # mark the lamps
        x_lamp = self.resolve_features(
            self.features_map_lamp,
            self.toolbox.data['lamps']
        )
        ones = np.ones((x_lamp.shape[0], 1))
        x_lamp = np.concatenate((x_lamp, ones), axis=1)
        y_lamp = x_lamp.dot(self.w_lamp.T)
        data = self.toolbox.data
        lamp_threshold = self.config['lamp_threshold']
        for i in range(len(y_lamp)):
            data['lamps'][i]['y'] = y_lamp[i]
        data['lamps'] = [l for l in data['lamps'] if l['y'] > lamp_threshold]
        # mark the pairs
        self.toolbox.match_pairs()
        x_pair = self.resolve_features(
            self.features_map_pair, self.toolbox.data['pairs'])
        ones = np.ones((x_pair.shape[0], 1))
        x_pair = np.concatenate((x_pair, ones), axis=1)
        y_pair = x_pair.dot(self.w_pair.T)
        for i in range(len(y_pair)):
            pair = data['pairs'][i]
            pair['y'] = y_pair[i]
            pair['y_max'] = np.max(y_pair[i])
            pair['y_label'] = np.argmax(y_pair[i])
            # debug
            if debug:
                pipe(
                    img.copy(),
                    self.toolbox.draw_contours,
                    self.toolbox.draw_bounding_rects,
                    self.toolbox.draw_pair_bounding_rects,
                    self.toolbox.draw_pair_index,
                    self.toolbox.draw_pair_bounding_text()(
                        lambda p: '{:.2f}'.format(p['y_max']),
                        text_position='bottom'
                    ),
                    curry(helpers.showoff)(timeout=timeout, update=True)
                )
            # will change in the future
        return self.toolbox

    def label(self, img, labels, debug=True):
        '''return (boolean) success'''
        self.calculate_lamps(img)
        self.toolbox.match_pairs()
        lamps = self.toolbox.data['lamps']

        pairs = self.toolbox.data['pairs']

        # save features to lamps and pairs
        x_lamp = self.resolve_features(
            self.features_map_lamp, self.toolbox.data['lamps'])
        x_pair = self.resolve_features(
            self.features_map_pair, self.toolbox.data['pairs'])
        for i in range(len(x_lamp)):
            lamps[i]['x'] = x_lamp[i, :].tolist()
        for i in range(len(x_pair)):
            pairs[i]['x'] = x_pair[i, :].tolist()
        # label the lamps
        for lamp in lamps:
            lamp['label'] = 0
            for labeled_rect in labels[0]:
                if self.__is_in(lamp['bounding_rect'], labeled_rect):
                    lamp['label'] = 1
                    break
        throw_false = 0
        new_pairs = []
        for pair in pairs:
            '''0->small, 1->large, 2->non'''
            pair['label'] = 2
            for labeled_pair in labels[1]:
                if self.__is_in(pair['bounding_rect'], labeled_pair):
                    pair['label'] = 0
                    break
                for labeled_pair in labels[2]:
                    if self.__is_in(pair['bounding_rect'], labeled_pair):
                        pair['label'] = 1
                        break
        # for labeled_pair in labels[3]:
        #     if self.__is_in(pair['bounding_rect'], labeled_pair):
        #         pair['label'] = 2
        #         break
        # for labeled_pair in labels[4]:
        #     if self.__is_in(pair['bounding_rect'], labeled_pair):
        #         pair['label'] = 2
        #         break
            if pair['label'] == 2:
                throw_false += 1
            if throw_false % 3 == 0 or pair['label'] < 2:
                new_pairs += [pair]
        self.toolbox.data['pairs'] = new_pairs
        return lamps, new_pairs

    def __is_in(self, rect, labeled_rect, margin=20):
        x, y, w, h = rect
        diff = abs(np.array([x, x+w, y, y+h]) - np.array(labeled_rect))
        return len(np.where(diff > margin)[0]) == 0


if __name__ == '__main__':
    predictor = Predictor()
    for i in range(0, 335, 1):
        img_url = 'data/test19/img{}.jpg'.format(i)
        print('Load {}'.format(img_url))
        img = helpers.load(img_url)
        predictor.predict(img, debug=True, timeout=100)
