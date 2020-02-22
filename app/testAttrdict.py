import autoaim

a = {'aa': 'aaa'}
b = autoaim.AttrDict({'aa': 'aaa'})


@autoaim.helpers.time_this
def use_dict():
    for i in range(150000):
        a = {'aa': 'aaa'}
        a['aa']


@autoaim.helpers.time_this
def use_attr():
    for i in range(150000):
        b = autoaim.AttrDict({'aa': 'aaa'})
        b.aa


@autoaim.helpers.time_this
def use_key():
    for i in range(150000):
        b = autoaim.AttrDict({'aa': 'aaa'})
        b['aa']


use_dict()
use_attr()
use_key()
