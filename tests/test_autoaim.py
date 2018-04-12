#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
import sys
sys.path.append('../')
from autoaim.autoaim import ImgToolbox


class TestAutoaim(unittest.TestCase):

    def setUp(self):
        self.autoaim = ImgToolbox('../data/miao1.jpg')

    def test_threshold(self):
        self.assertTrue(len(self.autoaim.threshold()) > 400)

    def test_findContours(self):
        contours, rects = self.autoaim.findContours()
        self.assertTrue(len(contours)==len(rects))
        self.assertTrue(len(contours)>80)

    def test_findLamps(self):
        lamps = self.autoaim.findLamps()
        self.assertTrue(len(lamps)>=2)

    def test_pairLamps(self):
        pair_lamps = self.autoaim.pairLamps()
        self.assertTrue(len(pair_lamps)==1)



if __name__ == '__main__':
    unittest.main()