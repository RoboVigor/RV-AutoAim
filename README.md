[![Build Status](https://travis-ci.com/RoboVigor/RV-AutoAim.svg?token=2Z1XgX7xLxVemPKXnupb&branch=v2)](https://travis-ci.com/RoboVigor/RV-AutoAim)

# RV AutoAim

再一次开始。

## Usage

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