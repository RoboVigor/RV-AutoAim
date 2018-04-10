# -*- coding: utf-8 -*-
import cv2
import os

mat = cv2.imread('../data/hotel.jpg')
cv2.imshow('Original Image', mat)
cv2.waitKey(0)