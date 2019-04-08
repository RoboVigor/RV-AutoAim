# -*- coding: utf-8 -*-
import unittest
import os
import serial
import serial.tools.list_ports
import autoaim

data1 = [87, 16, 0, 6, 0, 88]
port_list = list(serial.tools.list_ports.comports())

isTravis = bool(os.environ.get('TRAVIS_PYTHON_VERSION'))


class SerialTestSuite(unittest.TestCase):

    def test_crc_calculation(self):
        crc = autoaim.aaserial.crc_calculate(data1[1:4], 3)
        assert crc == 2

    def test_feature(self):
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
            if exit:
                break

    def test_predictor(self):
        for i in range(0, 5, 1):
            img_url = 'data/test8/img{}.jpg'.format(i)
            print('Load {}'.format(img_url))
            img = helpers.load(img_url)
            predictor = Predictor('weight8.csv')
            lamps = predictor.predict(img, mode='red', debug=True)
            lamps = [x for x in lamps if x.y > 0.5]
            print('   find {} lamp'.format(len(lamps)))

    @unittest.skipUnless(port_list and (not isTravis), 'No serial port available.')
    def test_serial_write_and_read(self):
        with serial.Serial('/dev/ttyTHS2', 9600, timeout=1) as ser:
            ser.write(bytearray(data1))
            x = ser.read(100)
        print([i for i in x])
        print(x)
        assert x


if __name__ == '__main__':
    unittest.main()
