# -*- coding: utf-8 -*-
import unittest
import sys
sys.path.append('../')
import xml.etree.ElementTree as ET
from autoaim.huaq import AimMat
import timeit


class TestAutoaim(unittest.TestCase):

    def setUp(self):
        self.autoaim = AimMat('../data/test0/img01.jpg')
        self.tests = [
            range(1, 7),  # basic
            range(1, 56), # 40-56 for large armor
            range(1, 38), # nightmare
            range(1, 16), # static
            range(1, 16), # drunk
            range(1, 15), # lab
            ]

    def _getLabel(self, test_index, str_i):
        try:
            tree = ET.ElementTree(file='../data/test'+str(test_index)+'/label/img'+str_i+'.xml')
        except:
            return [],[]
        root = tree.getroot()
        lamp_labels = []
        pair_labels = []
        for child in root:
            if child.tag == 'object':
                name = child[0].text
                rect = (child[4][0],child[4][2],child[4][1],child[4][3])#xmin,xmax,ymin,ymax
                rect = [int(x.text) for x in rect]
                #print(name, rect)
                if name == 'lamp':
                    lamp_labels += [rect]
                elif name == 'pair':
                    pair_labels += [rect]
        return lamp_labels, pair_labels

    def _autoTest(self, test_index):
        s1 = 0
        s2 = 0
        for i in self.tests[test_index]:
            str_i = '0'+str(i) if i<10 else str(i)
            autoaim = AimMat('../data/test'+str(test_index)+'/img'+str_i+'.jpg')
            lamp_labels, pair_labels = self._getLabel(test_index, str_i)
            s2 += len(pair_labels)
            marks = []
            ds1 = 0
            for pair in autoaim.pairs:
                mark = 0
                #print('  lamp:')
                for pair_label in pair_labels:
                    #print('    x diff',pair[0].x-pair_label[0])
                    if abs(pair[0].x-pair_label[0])<30:
                        mark = 100
                        ds1 += 1
                marks += [mark]
            ds1 = min([ds1,len(pair_labels)])
            s1 += ds1
            print('test'+str(test_index)+'/img'+str_i+'.jpg' )
            #print('  found lamps: ',len(autoaim.lamps),'/',len(lamp_labels))
            print('  found pairs: ',ds1,'/',len(pair_labels))
            print('  pairs marks:',marks)
        print('successfully paired: ',s1,'/',s2)

    def test_accuracy(self):
        self._autoTest(2)
        #pass
'''
    def test_speed(self):
        test_index = 0
        start = timeit.default_timer()
        # load
        # thresh
        threshes = []
        for i in self.tests[test_index]:
            str_i = '0'+str(i) if i<10 else str(i)
            autoaim = AimMat('../data/test'+str(test_index)+'/img'+str_i+'.jpg')
        duration = timeit.default_timer() - start
'''

if __name__ == '__main__':
    unittest.main()