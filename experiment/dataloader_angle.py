# -*- coding: utf-8 -*-
"""Data Loader Module

This module save the features to a csv file.

Author:
    tccoin
"""

import os
import csv
import math
import xml.etree.ElementTree as ET
import cv2
import numpy as np
import random
from toolz import pipe, curry
from autoaim import aimmat, AimMat, helpers, Predictor
import re

data_path = os.path.abspath(__file__ + '/../../data')

angle = [0,3,5,6,9,10,12,13,15,16,18,19,20,22,24,26,28,29,30,32,32,32,32,32,32,32,32,32,32,32,32,31,31,30,30,30,29,27,25,23,21,20,18,15,13,11,10,8,6,4,3,0,-1,-3,-5,-7,-9.5,-10,-13,-15,-18,-20,-20.5,-23,-24,-26,-29,-30,-31,-33,-35,-37,-38,-39,-39,-39,-39,-39,-39,-39,-39,-39,-38,-37,-36,-35,-34,-33,-32,-31,-30,-30,-29,-27,-26,-24,-23,-22,-21,-19.5,-17,-14,-12,-10,-9,-7.5,-5,-4,-3,-1,0,2,3,5,7,9.5,10,12,13,16,17,19,20,23,26,27,29.5,31,33,35,37,39,40,40,40,40,40,40,40,40,40,40,40,40,40,40,40,40,40,40,40,40,40,40,40,40,39.5,39,38,35,34,31,30,26,23,21,20,18,15,13,12,10,8,5,4,1,0,-4,-5,-7,-9,-11,-14,-15,-17,-19.5,-20.5,-23,-27,-29,-30,-31,-33,-35,-37,-39,-40,-40.5,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-41,-40,-40,-40,-39,-38,-37,-36,-34,-33,-32,-31,-30,-29,-28,-26,-24,-22,-21,-20,-19,-17,-16,-14,-13,-12,-11,-10,-9,-8,-7,-5,-4,-3,-2,-1,0,2,3,4,6,8,9.5,11,13,15,16,18,19.5,20,21,23,24,25,27,29,30,31,32,33,35,36,38,40,40,40,41,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42,42]

class DataLoader():

    def __init__(self, debug=False):
        self.debug = debug

    # ===================
    # Dataset Function
    # ===================

    def load_datasets(self, datasets, props, filename='test', cut=0.8):
        '''Example input:
        datasets = ['test0', 'test1', ...]
        props = ['contour', 'bounding_rect', ...]
        '''
        self.props = props
        header = self.generate_header()
        self.filename = filename
        self.new_csv(self.join('angle', 'train'), header)
        self.new_csv(self.join('angle', 'test'), header)
        for dataset in datasets:
            dataset_path = data_path+'/'+dataset
            files = [x for x in os.listdir(
                dataset_path) if os.path.isfile(dataset_path+'/'+x)]
            random.shuffle(files)
            cut_len = int(cut*len(files))
            self.load_images('train', dataset, files[0:cut_len])
            self.load_images('test', dataset, files[cut_len:-1])

    def load_images(self, data_type, dataset, images):
        global angle
        for image in images:
            aimmat = self.load_img(dataset, image)
            if aimmat:
                pair = aimmat.pairs[0]
                row = pair.anglex + [pair.angle]
                self.append_csv(self.join('angle', data_type), row)

    def load_img(self, dataset, image):
        '''return `exit`'''
        i = int(re.findall(r"\d+",os.path.splitext(image)[0])[0])
        print(i)
        # load image
        img_path = os.path.join(data_path, dataset, image)
        img = helpers.load(img_path)
        # predictor
        predictor = Predictor('model/weights/lamp.csv', 'model/weights/pair.csv', 'model/weights/angle.csv')
        aimmat = predictor.predict(img, mode='angle', debug=False,timeout=1000)
        if len(aimmat.pairs)>0:
            aimmat.pairs = [aimmat.pairs[0]]
            aimmat.pairs[0].angle = angle[i]
        return aimmat

    def load_label(self, dataset, file):
        labels = [[], [], []]  # lamp, small, large

        # load xml
        label = os.path.splitext(file)[0]
        label_path = os.path.join(
            data_path, dataset, 'label', label+'.xml')
        try:
            tree = ET.ElementTree(file=label_path)
        except:
            # print('>  Label file "{}"  not found!'.format(label_path))
            return labels
        root = tree.getroot()

        # classify
        for child in root:
            if child.tag == 'object':
                name = child[0].text
                rect = (child[4][0], child[4][2], child[4][1],
                        child[4][3])  # xmin,xmax,ymin,ymax
                rect = [int(x.text) for x in rect]
                if name == 'lamp':
                    labels[0].append(rect)
                elif name == 'pair1':
                    labels[1].append(rect)
                elif name == 'pair2':
                    labels[2].append(rect)
        return labels

    def __is_in(self, rect, labeled_rect):
        margin = 20
        x, y, w, h = rect
        diff = abs(np.array([x, x+w, y, y+h]) - np.array(labeled_rect))
        return len(np.where(diff > margin)[0]) == 0

    def join(self, str1, str2):
        return self.filename+'_'+str1+'_'+str2+'.csv'

    def generate_header(self):
        '''This method works together with aimmat.calcdict.'''
        row = []
        for props in self.props:
            if props in aimmat.calcdict:
                row += aimmat.calcdict[props].keys()
        row += ['bingo']
        return row

    # ===================
    # Debug Function
    # ===================

    def draw_bingo_lamps(self):
        '''Usage:dataloader.draw_bingo_lamps()(aimmat)'''
        def draw(aimmat, img):
            lamps = aimmat.lamps
            boom_rects = [x.bounding_rect for x in lamps if not x.bingo]
            bingo_rects = [x.bounding_rect for x in lamps if x.bingo]
            for rect in boom_rects:
                x, y, w, h = rect
                cv2.rectangle(img, (x, y), (x+w, y+h), (200, 0, 200), 1)
            for rect in bingo_rects:
                x, y, w, h = rect
                cv2.rectangle(img, (x, y), (x+w, y+h), (200, 0, 0), 2)
            return img
        return curry(draw)

    def draw_labeled_lamps(self):
        '''Usage:dataloader.draw_labeled_lamps()(rects)'''
        def draw(rects, img):
            for rect in rects:
                xmin, xmax, ymin, ymax = rect
                cv2.rectangle(img, (xmin, ymin), (xmax, ymax),
                              (0, 0, 200), 3)
            return img
        return curry(draw)

    # ===================
    # CSV Function
    # ===================

    def new_csv(self, filename, row):
        '''Create a new scv file and write the table's header to it.'''
        with open(data_path + '/'+filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=' ',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(row)

    def append_csv(self, filename, row):
        with open(data_path + '/'+filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=' ',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(row)

    def read_csv(self, filename):
        with open(data_path + '/'+filename, 'r') as csvfile:
            rows = list(csv.reader(csvfile))
            header = rows[:1][0][0].split(' ')
            table = [[float(item) for item in row[0].split(' ')]
                     for row in rows[1:]]
            return header, table


if __name__ == '__main__':
    props = aimmat.enabled_props
    datasets = [
        'test17',
    ]
    dataloader = DataLoader(debug=True)
    dataloader.load_datasets(datasets, props)
