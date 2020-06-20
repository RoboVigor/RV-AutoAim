# -*- coding: utf-8 -*-
import unittest
import os
import autoaim
from autoaim import *
from toolz import pipe, curry

data1 = [0xA5, 0x03, 0x00, 0x3E, 0x86, 0x01,
         0x00, 0x01, 0xBC, 0x02, 0x0F, 0x74]

isTravis = bool(os.environ.get('TRAVIS_PYTHON_VERSION'))


class AutoAimTestSuite(unittest.TestCase):

    def test_crc8_checksum(self):
        crc = telegram.get_crc8_checksum(data1[0:4])
        assert crc == data1[4]

    def test_crc16_checksum(self):
        crc = telegram.get_crc16_checksum(data1[0:10])
        assert crc == (data1[10]+(data1[11] << 8))

    def test_telegram_pack(self):
        test_packet = telegram.pack(
            0x0001, [bytes([0x01, 0xBC, 0x02])], seq=0x3E)
        assert bytes(data1) == test_packet

    def test_telegram_unpack(self):
        unpacker = telegram.Unpacker()
        info = {}
        for byte in bytes(data1):
            info = unpacker.send(byte)
        assert info['state'] == 'EOF'

    @unittest.skipUnless(telegram.port_list and (not isTravis), 'No serial port available.')
    def test_telegram_send(self):
        print('--- telegram ---')
        x = telegram.send(bytearray(data1))
        print(x)
        assert x

    def test_toolbox(self):
        '''calculate features using test18'''
        for i in range(0, 5, 1):
            img_url = 'data/test18/img{}.jpg'.format(i)
            img = helpers.load(img_url)
            config = Config().data
            toolbox = Toolbox(config)
            pipe(img,
                 toolbox.start,
                 toolbox.split_rgb,
                 toolbox.find_contours,
                 toolbox.calc_features,
                 toolbox.match_pairs
                 )

    def test_predictor(self):
        '''predicte using test18'''
        for i in range(0, 5, 1):
            img_url = 'data/test18/img{}.jpg'.format(i)
            img = helpers.load(img_url)
            predictor = Predictor()
            predictor.predict(img, debug=False)
            toolbox = predictor.toolbox
            lamps = toolbox.data['lamps']
            lamps = [x for x in lamps if x['y'] > 0.5]

    @helpers.time_this
    def test_fps(self):
        '''predict 100 image from test18'''
        for i in range(0, 100, 1):
            img_url = 'data/test18/img{}.jpg'.format(i)
            img = helpers.load(img_url)
            predictor = Predictor()
            predictor.predict(img, debug=False)
            toolbox = predictor.toolbox
            lamps = toolbox.data['lamps']
            lamps = [x for x in lamps if x['y'] > 0.5]


if __name__ == '__main__':
    unittest.main()
