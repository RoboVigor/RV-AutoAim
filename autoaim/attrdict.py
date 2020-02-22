# -*- coding: utf-8 -*-

import json


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

    def save(self, path):
        with open(path, 'w') as json_file:
            json_file.write(json.dumps(self.data))
        return self

    def read(self, path):
        with open(path, 'r') as json_file:
            self.data.update(json.loads(json_file.read()))
            # super().__setattr__('data', json.loads(json_file.read()))
        return self

    def update(self, data):
        self.data.update(data)


class Lamp():
    def __init__(self, contour):
        super().__init__({
            'contour': contour
        })


class Pair():
    def __init__(self, left, right):
        super().__init__({
            'left': left,
            'right': right
        })


class Config():
    def __init__(self, config={}):
        self.data = {}
        self.read('default')
        self.update(config)

    def save(self, config_name=None):
        if config_name is None:
            config_name = self.data['config_name']
        path = 'configs/'+config_name+'.json'
        # todo
        return self

    def read(self, config_name=None):
        if config_name is None:
            config_name = self.data['config_name']
        path = 'configs/'+config_name+'.json'
        with open(path, 'r') as json_file:
            self.data.update(json.loads(json_file.read()))
        return self

    def update(self, data):
        self.data.update(data)
        return self


if __name__ == '__main__':
    config = Config().read('infantry')
    config.update({'target_color': 'blue'})
    print(config.data)
    # config.save()
