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
from toolz import pipe, curry
from autoaim import Feature, helpers

data_path = os.path.abspath(__file__ + '/../../data')


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


class DataLoader():
    ''' @todo: finish implementation of __calcdict
        @todo: rotated_rect_angle have some problems
    '''
    __calcdict = {
        'contour': {
            'contour_len': lambda x: len(x)
        },
        'bounding_rect': {
            # 'bounding_rect_w': lambda x: x[0],
            # 'bounding_rect_y': lambda x: x[1],
            'bounding_rect_ratio': lambda x: (x[0]/x[1]) if x[1] else 0
        },
        'rotated_rect': {
            'rotated_rect_angle': lambda x: -x[2]/90,
        },
        'greyscale': {
            'greyscale': lambda x: x/255,
        },
        'point_area': {
            'point_area': lambda x: x,
        },
        'bingo': {
            'bingo': lambda x: int(x),
        },
    }

    def __init__(self, csv_filename, debug=False):
        self.csv_path = data_path + '/' + csv_filename
        self.debug = debug

    def load_datasets(self, datasets, feature_bucket):
        '''Example input:
        datasets = ['test0', 'test1', ...]
        feature_bucket = ['contour', 'bounding_rect', ...]
        '''
        self.feature_bucket = feature_bucket
        self.new_csv()
        for dataset in datasets:
            self.load_dataset(dataset)

    def load_dataset(self, dataset):
        dataset_path = data_path+'/'+dataset
        files = os.listdir(dataset_path)
        for file in files:
            file_path = dataset_path+'/'+file
            if os.path.isfile(file_path):
                if self.load_img(dataset, file):
                    break

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

    def load_img(self, dataset, file):
        '''return `exit`'''
        # load labels
        labels = self.load_label(dataset, file)
        if labels is None:
            return False
        else:
            labeled_lamps, labeled_pairs = labels
        # load image
        img_path = os.path.join(data_path, dataset, file)
        img = helpers.load(img_path)
        # calc features
        feature = Feature(img)
        feature.bounding_rects, feature.point_areas
        for feature_name in self.feature_bucket:
            getattr(feature, feature_name+'s', '')
        lamps = feature.lamps
        # label the real-time feature
        for lamp in lamps:
            lamp.bingo = False
            for labeled_lamp in labeled_lamps:
                if self.__is_in(lamp.bounding_rect, labeled_lamp):
                    lamp.bingo = True
                    break
        print('{}/{}: {} lamps'.format(dataset, file, len(lamps)))
        self.append_csv(feature)
        if self.debug:
            exit = pipe(img.copy(),
                        # feature.draw_contours,
                        feature.draw_bounding_rects,
                        self.draw_labeled_lamps()(labeled_lamps),
                        self.draw_bingo_lamps()(feature),
                        helpers.showoff
                        )
            return exit
        else:
            return False

    def __is_in(self, rect, labeled_rect):
        margin = 15
        x, y, w, h = rect
        diff = abs(np.array([x, x+w, y, y+h]) - np.array(labeled_rect))
        return len(np.where(diff > margin)[0]) == 0

    def generate_csv_row(self, lamp=None):
        '''This method works together with calcdict.'''
        calcdict = self.__calcdict
        row = []
        if lamp is None:
            for feature_name in self.feature_bucket:
                if feature_name in calcdict:
                    row += calcdict[feature_name].keys()
        else:
            for feature_name in self.feature_bucket:
                if feature_name in calcdict:
                    for func in calcdict[feature_name].values():
                        row.append(func(getattr(lamp, feature_name)))
        return row

    def new_csv(self):
        '''Create a new scv file and write the table's header to it.'''
        with open(self.csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=' ',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            row = self.generate_csv_row()
            writer.writerow(row)

    def append_csv(self, feature):
        with open(self.csv_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=' ',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for lamp in feature.lamps:
                row = self.generate_csv_row(lamp)
                writer.writerow(row)

    def read_csv(self):
        with open(self.csv_path, 'r') as csvfile:
            rows = [*csv.reader(csvfile)]
            header = rows[:1][0][0].split(' ')
            table = [[float(item) for item in row[0].split(' ')]
                     for row in rows[1:]]
            return header, table

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


if __name__ == '__main__':
    feature_bucket = [
        'contour',
        'bounding_rect',
        'rotated_rect',
        'greyscale',
        'point_area',
        'bingo'
    ]
    datasets = [
        # 'test0',
        'test5',
        'test6',
    ]
    dataloader = DataLoader('train.csv', debug=False)
    dataloader.load_datasets(datasets, feature_bucket)
    datasets = [
        'test0',
    ]
    dataloader = DataLoader('test.csv', debug=False)
    dataloader.load_datasets(datasets, feature_bucket)
