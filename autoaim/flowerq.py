import cv2
import numpy as np
from huaq import AimMat

autoaim = AimMat('../data/test0/img01.jpg')
autoaim.showoff('miao '*3)
print(autoaim.pairs)
cv2.waitKey(0)