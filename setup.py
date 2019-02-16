# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages

with open('LICENSE') as f:
    license = f.read()

setup(
    name='AutoAim',
    version='2.0.1',
    description='Autoaim scripts for RoboMaster',
    author='FuXing PS',
    author_email='robovigor@gmail.com',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
