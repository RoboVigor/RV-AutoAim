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
            range(1, 7),   # 0.basic
            range(1, 56), # 1.large armor in 40-56
            range(1, 38),  # 2.nightmare
            range(1, 16),  # 3.static
            range(1, 16),  # 4.drunk
            range(1, 13),  # 5.lab (bad env)
            range(1, 23),  # 6.lab
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
        s1 = 0 # successful pairs
        s2 = 0 # total pairs labeled
        s3 = 0 # total lamp found
        for i in self.tests[test_index]:
            str_i = '0'+str(i) if i<10 else str(i)
            autoaim = AimMat('../data/test'+str(test_index)+'/img'+str_i+'.jpg')
            s3 += len(autoaim)
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
            #print('test'+str(test_index)+'/img'+str_i+'.jpg' )
            #print('  found lamps: ',len(autoaim.lamps),'/',len(lamp_labels))
            #print('  found pairs: ',ds1,'/',len(pair_labels))
            #print('  pairs marks:',marks)
        print('test ',test_index)
        print('  successfully paired: ',s1,'/',s2)
        print('  found lamps:',s3)

    def test_accuracy(self):
        for i in range(0,7):
            self._autoTest(i)
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