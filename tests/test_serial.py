# -*- coding: utf-8 -*-

import unittest
import serial
from context import autoaim

data1 = [87, 16, 0, 6, 0, 88]


class SerialTestSuite(unittest.TestCase):

    def test_crc_calculation(self):
        crc = autoaim.aaserial.crc_calculate(data1[1:4], 3)
        assert crc == 2

    def test_serial_write_and_read(self):
        with serial.Serial('/dev/ttyTHS2', 9600, timeout=1) as ser:
            ser.write(bytearray(data1))
            x = ser.read(100)
        print([i for i in x])
        print(x)
        assert x


if __name__ == '__main__':
    unittest.main()
