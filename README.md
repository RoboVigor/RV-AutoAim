[![Build Status](https://travis-ci.com/RoboVigor/RV-AutoAim.svg?token=2Z1XgX7xLxVemPKXnupb&branch=v2)](https://travis-ci.com/RoboVigor/RV-AutoAim) [![Package version](https://badge.fury.io/gh/RoboVigor%2FRV-AutoAim.svg)](https://badge.fury.io/gh/RoboVigor%2FRV-AutoAim)

# RV AutoAim

再一次开始。

## Install

```bash
# install basic requirements
conda create -n cv numpy opencv pytorch torchvision cudatoolkit=9.0 python=3.7 --channel menpo opencv
conda activate cv
pip install -r requirements.txt
bash install.sh
# install developing requirements
conda install jupyterlab -c conda-forge
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
     #  aimmat.draw_texts()('greyscale'),
     helpers.showoff
     )
```

## Specification

## 帧结构

| Name | Length | Description   | Value(DEC) |
| ---- | ------ | ------------- | ---------- |
| SOF  | 8      | 起始段        | 87         |
| ID   | 4      | 数据ID        | 0-15       |
| LEN  | 4      | 数据长度n     | 0-15       |
| DATA | 16n    | uint16        |            |
| CRC8 | 8      | 检验段 |            |
| EOF  | 8      | 结束段        | 88         |

已废除，通讯协议见`/docs/RM2019裁判系统用户接口协议附录 V1.1.pdf`

## Contribute

### Python 风格

参考[Google 开源项目风格指南](https://zh-google-styleguide.readthedocs.io/en/latest/google-python-styleguide/python_style_rules/#id16)

```
module_name, package_name, ClassName, method_name, ExceptionName, function_name, GLOBAL_VAR_NAME, instance_var_name, function_parameter_name, local_var_name.
```
