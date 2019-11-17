#!/usr/bin/env python3
from distutils.core import setup

setup(name='udebs',
      package_data={'udebs': ['keywords/*.json']},
      version='1.0',
      description='Python game analysis engine',
      author='Ryan Chartier',
      author_email='redrecrm@gmail.com',
#       url='https://www.python.org/sigs/distutils-sig/',
      packages=['udebs'],
     )