#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import numpy


def load(img):
    """automatically load image from str or array"""
    if isinstance(img, str):
        src = cv2.imread(img)
    elif isinstance(img, np.ndarray):
        src = img
    else:
        raise Exception('helpers.load Error: Wrong input.')
    if src is None:
        raise Exception('autoaim.feature Error: Image loading failed.')
    return src


def showoff(img):
    """an easy way to show image, return `exit`"""
    cv2.imshow('showoff', img)
    key = cv2.waitKey(0)
    cv2.destroyAllWindows()
    if key == 27:
        return True
    return False


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


if __name__ == '__main__':
    img = load('data/test0/img02.jpg')
    showoff(img)
