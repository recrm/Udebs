#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(name='udebs',
      package_data={'udebs': ['keywords/*.json']},
      version='1.0',
      description='Python game analysis engine',
      author='Ryan Chartier',
      author_email='redrecrm@gmail.com',
#       url='https://www.python.org/sigs/distutils-sig/',
      packages=find_packages(),
      scripts=[
        "demos/udebs_hex",
        "demos/udebs_life",
        "demos/udebs_rps",
        "demos/udebs_tictactoe"
      ],
      zip_safe=False,
      python_requires=">=3.6",
     )
