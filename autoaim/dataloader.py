# -*- coding: utf-8 -*-
"""Data Loader Module

This module save the features to a csv file.

Author:
    tccoin
"""
import os
import math
import xml.etree.ElementTree as ET
import cv2
import numpy as np
import random
from toolz import pipe, curry
from autoaim import Toolbox, helpers, Config, Predictor


class DataLoader():

    def __init__(self, config=None):
        if config is None:
            config = Config().data
        predictor = Predictor(config.data)
        self.config = config.data
        self.predictor = predictor
        self.toolbox = predictor.toolbox

    # ===================
    # Dataset Function
    # ===================

    def generate_datasets(self, datasets, cut=0.9, seed=42):
        '''Example input:
        datasets = ['test0', 'test1', ...]
        '''
        self.filename = self.config['config_name']
        header_lamp = self.predictor.generate_header(
            self.predictor.features_map_lamp) + ['label']
        header_pair = self.predictor.generate_header(
            self.predictor.features_map_pair) + ['label']
        helpers.new_csv(self.join('lamp', 'train'), header_lamp)
        helpers.new_csv(self.join('lamp', 'test'), header_lamp)
        helpers.new_csv(self.join('pair', 'train'), header_pair)
        helpers.new_csv(self.join('pair', 'test'), header_pair)
        for dataset in datasets:
            dataset_path = 'data/'+dataset
            files = [x for x in os.listdir(
                dataset_path) if os.path.isfile(dataset_path+'/'+x)]
            if seed is not None:
                random.seed(seed)
            random.shuffle(files)
            cut_len = int(cut*len(files))
            self.process_images('train', dataset, files[0:cut_len])
            self.process_images('test', dataset, files[cut_len:-1])

    def process_images(self, data_type, dataset, images):
        for image_name in images:
            print(dataset+'/'+image_name)
            img = helpers.load('data/'+dataset+'/'+image_name)
            labeled_rects = self.load_label(dataset, image_name)
            lamps, pairs = self.predictor.label(img, labeled_rects)
            for lamp in lamps:
                row = lamp['x'] + [int(lamp['label'])]
                helpers.append_csv(self.join('lamp', data_type), row)
            for pair in pairs:
                row = pair['x'] + [int(pair['label'])]
                helpers.append_csv(self.join('pair', data_type), row)

    def load_label(self, dataset, file_name):
        # lamp, small-pair, large-pair, not-small-pair, not-large-pair, not-pair
        labels = [[] for i in range(5)]

        # load xml
        label = os.path.splitext(file_name)[0]
        label_path = os.path.join(
            'data', dataset, 'label', label+'.xml')
        try:
            tree = ET.ElementTree(file=label_path)
        except:
            print('>  Label file "{}"  not found!'.format(label_path))
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
                # if name == 'notpair1':
                #     labels[3].append(rect)
                #     labels[5].append(rect)
                # if name == 'notpair2':
                #     labels[4].append(rect)
                #     labels[5].append(rect)
        return labels

    def join(self, str1, str2):
        return self.filename+'_'+str1+'_'+str2+'.csv'

    # ===================
    # Debug Function
    # ===================

    def draw_label_lamps(self):
        '''Usage:dataloader.draw_label_lamps()(aimmat)'''
        def draw(aimmat, img):
            lamps = aimmat.lamps
            boom_rects = [x['bounding_rect'] for x in lamps if not x['label']]
            label_rects = [x['bounding_rect'] for x in lamps if x['label']]
            for rect in boom_rects:
                x, y, w, h = rect
                cv2.rectangle(img, (x, y), (x+w, y+h), (200, 0, 200), 1)
            for rect in label_rects:
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


if __name__ == '__main__':
    datasets = [
        # 'test18',
        # 'test19',
        # 'test20',
        'test11',
        'test12'
    ]
    config = Config()
    dataloader = DataLoader(config)
    dataloader.generate_datasets(datasets)
