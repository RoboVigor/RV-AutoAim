# -*- coding: utf-8 -*-

from os import path
import csv
import cv2
import numpy as np
import numpy
from functools import wraps
# from matplotlib import pyplot as plt


def load(img):
    """automatically load image from str or array"""
    if isinstance(img, str):
        src = cv2.imread(img)
    elif isinstance(img, np.ndarray):
        src = img
    else:
        raise Exception('helpers.load Error: Wrong input.')
    if src is None:
        raise Exception('autoaim.aimmat Error: Image loading failed.')
    return src


def peek(img, timeout=0, update=False):
    """an easy way to show image, return img"""
    cv2.imshow('showoff', img)
    key = cv2.waitKey(timeout)
    return img


def showoff(img, timeout=0, update=False):
    """an easy way to show image, return `exit`"""
    cv2.imshow('showoff', img)
    key = cv2.waitKey(timeout)
    if not update:
        cv2.destroyAllWindows()
    if key == 27:
        return True
    return False


def color(img):
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)


# def pltshow(img):
#     """an easy way to show image with matplotlib"""
#     plt.imshow(img[..., ::-1])
#     plt.show()

def time_this(original_function):
    """timing decorators for a function"""
    print("decorating")

    def new_function(*args, **kwargs):
        print("starting timer")
        import datetime
        before = datetime.datetime.now()
        x = original_function(*args, **kwargs)
        after = datetime.datetime.now()
        print("Elapsed Time = {0}".format(after-before))
        return x
    return new_function


def time_all_class_methods(Cls):
    """timing decorators for a class"""
    class NewCls:
        def __init__(self, *args, **kwargs):
            self.oInstance = Cls(*args, **kwargs)

        def __getattribute__(self, s):
            try:
                x = super(NewCls, self).__getattribute__(s)
            except AttributeError:
                pass
            else:
                return x
            x = self.oInstance.__getattribute__(s)
            if type(x) == type(self.__init__):
                return time_this(x)
            else:
                return x
    return NewCls


def coroutine(func):
    """Prime the coroutine"""
    @wraps(func)
    def primer(*args, **kwargs):
        gen = func(*args, **kwargs)
        next(gen)
        return gen
    return primer


main_dir = path.abspath(path.dirname(__file__) + '/..')+'/'


def new_csv(filename, row=''):
    '''Create a new csv file and write the table's header to it.'''
    with open(main_dir+filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(row)


def append_csv(filename, row=''):
    with open(main_dir+filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(row)


def read_csv(filename):
    with open(main_dir+filename, 'r') as csvfile:
        rows = list(csv.reader(csvfile))
        header = rows[0]
        table = [[float(y) for y in x] for x in rows[1:]]
        return header, table


if __name__ == '__main__':
    img = load('data/test18/img0.jpg')
    showoff(img)
