[![Build Status](https://travis-ci.com/RoboVigor/RV-AutoAim.svg?token=2Z1XgX7xLxVemPKXnupb&branch=v2)](https://travis-ci.com/RoboVigor/RV-AutoAim) [![Package version](https://badge.fury.io/gh/RoboVigor%2FRV-AutoAim.svg)](https://badge.fury.io/gh/RoboVigor%2FRV-AutoAim)

# RV AutoAim

再再一次开始。

## Install

```bash
# install basic requirements
conda create -n cv numpy opencv pytorch torchvision cudatoolkit=9.0 python=3.7 -c menpo opencv
conda activate cv
pip install -r requirements.txt
bash install.sh
# install developing requirements
conda install jupyterlab -c conda-forge
pip install PyQt5
```

### Usage

```python
from autoaim import *

# load an image
img = helpers.load('../data/test7/img1.jpg')

# make the prediction
predictor = Predictor('weight.csv')
predictor.predict(img, mode='red')

# extract aimmats
aimmat = AimMat(img)
print('find {} contours'.format(len(aimmat.contours)))
pipe(img.copy(),
     aimmat.draw_contours,
     #  aimmat.draw_bounding_rects,
     aimmat.draw_rotated_rects,
     #  aimmat.draw_ellipses,
     aimmat.draw_texts()('point_area'),
     #  aimmat.draw_texts()('grayscale'),
     helpers.showoff
     )
```

## Specification

## 帧结构

见`/docs/RM2019裁判系统用户接口协议附录 V1.1.pdf`

## Contribute

### 协作方式
AutoAim从v3开始将区分库维护者和用户，前者主要负责维护autoaim库中的接口和算法实现，后者主要使用autoaim库对各兵种进行调试。

### Python 风格

参考[Google 开源项目风格指南](https://zh-google-styleguide.readthedocs.io/en/latest/google-python-styleguide/python_style_rules/#id16)

```
module_name, package_name, ClassName, method_name, ExceptionName, function_name, GLOBAL_VAR_NAME, instance_var_name, function_parameter_name, local_var_name.
```
