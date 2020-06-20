# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages

with open('LICENSE') as f:
    license = f.read()

setup(
    name='autoaim',
    version='3.2.1',
    description='A project for detecting armors.',
    author='FuXing PS',
    author_email='robovigor@gmail.com',
    install_requires=[
        'pyserial>=3.4',
        'toolz>=0.9.0',
        'numpy'
    ],
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
