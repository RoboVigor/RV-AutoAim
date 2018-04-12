# 低科技自瞄外挂

来，携手共进，开发属于我们的自瞄外挂！

[开发日志](https://note.krrr.party/#/article/article-792559)
## Usage

```python
autoaim = ImgToolbox('path/to/img')
autoaim.mat = autoaim.r # use the green channel (default)
autoaim.drawMat = autoaim.src # use the source image to draw (default)
autoaim.pairLamps(True) # use the method while drawing
autoaim.show('o'*8+'h')
```

## ImgToolbox

```python
threshold(draw=False)
findContours(draw=False, thresh=None)
findLamps(draw=False, contours=None, rects=None)
pairLamps(draw=False, lamps=None)
```

## 目录

```
LICENSE
README.md
requirements.txt
docs/
tests/
data/
autoaim/
```
- `docs/` 存放一些文档
- `tests/` 单元测试
- `data/` 一些用于识别测试的照片
- `autoaim/` 核心科技

## 许可

MIT

2018, Fu Xing PS