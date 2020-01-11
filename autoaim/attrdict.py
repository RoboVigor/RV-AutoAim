# -*- coding: utf-8 -*-
class AttrDict(object):
    """
    This class supports both . and [] operators.
    Use . in most cases and only use [] when fetching data in large batch.
    """

    def __init__(self, mapping={}):
        super().__setattr__('data', dict(mapping))

    def __setattr__(self, attr, value):
        self.data[attr] = value

    def __getattr__(self, attr):
        if hasattr(self.data, attr):
            return getattr(self.data, attr)
        else:
            try:
                return self.data[attr]
            except KeyError:
                raise AttributeError

    def __getitem__(self, key):
        return self.data[key]


# for key in sorted(mydict.keys()):
#     print("%s: %s" % (key, mydict[key]))


class Lamp(AttrDict):
    def __init__(self, contour):
        super().__init__({
            'contour': contour
        })


class Pair(AttrDict):
    def __init__(self, left, right):
        super().__init__({
            'left': left,
            'right': right
        })


class Config(AttrDict):
    def __init__(self, config={}):
        _config = {
            # camera
            'camera_config': '',
            # toolbox
            'target_color': 'red',
            'binary_threshold_value': None,
            'binary_threshold_scale': 0.1,
            'rect_area_threshold': (32, 16384),
            'hsv_lower_value': 46,
            'free_scaling_parameter': 0,
            'point_area_threshold': (32, 8192),
            'max_contour_len': 100,
            'features': ['bounding_rect', 'rotated_rect', 'ellipse', 'contour_feature', 'angle'],
            'camera_matrix': [
                [1404.301464037759, 0, 615.802069602196],
                [0, 1408.256656922631, 339.7994434183557],
                [0, 0, 1]
            ],
            'distortion_coefficients': [-0.4432836554055214, 0.44834903270408, -0.0008076318909730519, -0.004013115215051138, 0.8668211330541649],
            # predictor
            'lamp_threshold': 0.5,
            'lamp_weight': 'lamp.csv',
            'pair_weight': 'pair.csv',
        }
        _config.update(config)
        super().__init__(_config)
