# -*- coding: utf-8 -*-
import unittest
import os
import autoaim
from autoaim import *

data1 = [87, 16, 0, 6, 0, 88]

isTravis = bool(os.environ.get('TRAVIS_PYTHON_VERSION'))

class AutoAimTestSuite(unittest.TestCase):

    def test_crc_calculation(self):
        crc = telegram.crc_calculate(data1[1:4], 3)
        assert crc == 2

    def test_feature(self):
        print('--- feature ---')
        for i in range(0, 5, 1):
            img_url = 'data/test8/img{}.jpg'.format(i)
            print('Load {}'.format(img_url))
            img = helpers.load(img_url)
            feature = Feature(img)
            feature.calc([
                'contours',
                'bounding_rects',
                'rotated_rects',
                'greyscales',
                'point_areas',
            ])
            print('   find {} contours'.format(len(feature.contours)))

    def test_predictor(self):
        print('--- predictor ---')
        for i in range(0, 5, 1):
            img_url = 'data/test8/img{}.jpg'.format(i)
            print('Load {}'.format(img_url))
            img = helpers.load(img_url)
            predictor = Predictor('weight8.csv')
            lamps = predictor.predict(img, mode='red', debug=False)
            lamps = [x for x in lamps if x.y > 0.5]
            print('   find {} lamp'.format(len(lamps)))

    # @helpers.time_this
    # def test_fps(self):
    #     print('--- predict 100 image from test8 ---')
    #     for i in range(0, 100, 1):
    #         img_url = 'data/test8/img{}.jpg'.format(i)
    #         print('Predict {}'.format(img_url))
    #         img = helpers.load(img_url)
    #         predictor = Predictor('weight8.csv')
    #         lamps = predictor.predict(img, mode='red', debug=False)
    #         lamps = [x for x in lamps if x.y > 0.5]

    @helpers.time_this
    def test_fps(self):
        print('--- predict 100 image from test8 ---')
        for i in range(0, 100, 1):
            img_url = 'data/test8/img{}.jpg'.format(i)
            print('Feature: {}'.format(img_url))
            img = helpers.load(img_url)
            feature = Feature(img)
            feature.calc([
                'contours',
                'bounding_rects',
                'rotated_rects',
            ])

    @unittest.skipUnless(telegram.port_list and (not isTravis), 'No serial port available.')
    def test_telegram(self):
        print('--- telegram ---')
        x = telegram.send(bytearray(data1))
        print(x)
        assert x


if __name__ == '__main__':
    unittest.main()
