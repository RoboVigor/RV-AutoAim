# -*- coding: utf-8 -*-
import cv2
import os

mat = cv2.imread('../data/hotel.jpg')
b, g, r = cv2.split(mat)
cv2.imshow('Original', mat)
ret, thresh = cv2.threshold(b, 20, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
canny = cv2.Canny(b, 50, 150)
cv2.imshow('threshold', thresh)
cv2.imshow('canny', canny)
cv2.waitKey(0)
cv2.destroyAllWindows()