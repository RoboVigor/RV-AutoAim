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
from autoaim import feature, Feature, helpers

data_path = os.path.abspath(__file__ + '/../../data')


class DataLoader():

    def __init__(self, debug=False):
        self.debug = debug

    # ===================
    # Dataset Function
    # ===================

    def load_datasets(self, datasets, props, train_filename='train.csv', test_filename='test.csv', cut=0.7):
        '''Example input:
        datasets = ['test0', 'test1', ...]
        props = ['contour', 'bounding_rect', ...]
        '''
        self.props = props
        header = self.generate_header()
        self.new_csv(train_filename, header)
        self.new_csv(test_filename, header)
        for dataset in datasets:
            dataset_path = data_path+'/'+dataset
            files = [x for x in os.listdir(
                dataset_path) if os.path.isfile(dataset_path+'/'+x)]
            random.shuffle(files)
            cut_len = int(cut*len(files))
            self.load_images(train_filename, dataset, files[0:cut_len])
            self.load_images(test_filename, dataset, files[cut_len:-1])

    def load_images(self, csv, dataset, images):
        for image in images:
            feature = self.load_img(dataset, image)
            if feature:
                for lamp in feature.lamps:
                    row = [x for x in lamp.x.values()] + [int(lamp.bingo)]
                    self.append_csv(csv, row)

    def load_img(self, dataset, image):
        '''return `exit`'''
        props = self.props + ['bounding_rect']
        # load labels
        labels = self.load_label(dataset, image)
        if labels is None:
            labeled_lamps, labeled_pairs = [], []
        else:
            labeled_lamps, labeled_pairs = labels
        # load image
        img_path = os.path.join(data_path, dataset, image)
        img = helpers.load(img_path)
        # calc features
        feature = Feature(img)
        feature.calc(props)
        # label the lamps
        lamps = feature.lamps
        for lamp in lamps:
            lamp.bingo = False
            for labeled_lamp in labeled_lamps:
                if self.__is_in(lamp.bounding_rect, labeled_lamp):
                    lamp.bingo = True
                    break
        print('{}/{}: {} lamps'.format(dataset, image, len(lamps)))
        if self.debug:
            pipe(img.copy(),
                 # feature.draw_contours,
                 feature.draw_bounding_rects,
                 self.draw_labeled_lamps()(labeled_lamps),
                 self.draw_bingo_lamps()(feature),
                 helpers.showoff
                 )
        return feature

    def load_label(self, dataset, file):
        label = os.path.splitext(file)[0]
        label_path = os.path.join(
            data_path, dataset, 'label', label+'.xml')
        try:
            tree = ET.ElementTree(file=label_path)
        except:
            print('>  Label file "{}"  not found!'.format(label_path))
            return None
        root = tree.getroot()
        lamps = []
        pairs = []
        for child in root:
            if child.tag == 'object':
                name = child[0].text
                rect = (child[4][0], child[4][2], child[4][1],
                        child[4][3])  # xmin,xmax,ymin,ymax
                rect = [int(x.text) for x in rect]
                if name == 'lamp':
                    lamps.append(rect)
                elif name == 'pair':
                    pairs.append(rect)
        return lamps, pairs

    def __is_in(self, rect, labeled_rect):
        margin = 15
        x, y, w, h = rect
        diff = abs(np.array([x, x+w, y, y+h]) - np.array(labeled_rect))
        return len(np.where(diff > margin)[0]) == 0

    def generate_header(self):
        '''This method works together with feature.calcdict.'''
        row = []
        for props in self.props:
            if props in feature.calcdict:
                row += feature.calcdict[props].keys()
        row += ['bingo']
        return row

    # ===================
    # Debug Function
    # ===================

    def draw_bingo_lamps(self):
        '''Usage:dataloader.draw_bingo_lamps()(feature)'''
        def draw(feature, img):
            lamps = feature.lamps
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
    props = feature.enabled_props
    datasets = [
        'test8',
        'test9',
    ]
    dataloader = DataLoader(debug=False)
    dataloader.load_datasets(datasets, props)
