[![Build Status](https://travis-ci.com/RoboVigor/RV-AutoAim.svg?token=2Z1XgX7xLxVemPKXnupb&branch=v2)](https://travis-ci.com/RoboVigor/RV-AutoAim)

[![Package version](https://badge.fury.io/gh/RoboVigor%2FRV-AutoAim.svg)](https://badge.fury.io/gh/RoboVigor%2FRV-AutoAim)

# RV AutoAim

再一次开始。

## Install

```bash
conda create -n cv numpy opencv python=3.6
source activate cv
pip install -r requirements.txt
```

### Usage

```python
from autoaim import *

# load an image
img = helpers.load('data/test0/img02.jpg')

# show the image
helpers.showoff(img)

# extract features
feature = Feature(img)
print('find {} contours'.format(len(feature.contours)))
pipe(img.copy(),
     feature.draw_contours,
     #  feature.draw_bounding_rects,
     feature.draw_rotated_rects,
     #  feature.draw_ellipses,
     feature.draw_texts()('point_area'),
     #  feature.draw_texts()('greyscale'),
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

## Contribute

### Python 风格

参考[Google 开源项目风格指南](https://zh-google-styleguide.readthedocs.io/en/latest/google-python-styleguide/python_style_rules/#id16)

```
module_name, package_name, ClassName, method_name, ExceptionName, function_name, GLOBAL_VAR_NAME, instance_var_name, function_parameter_name, local_var_name.
```
