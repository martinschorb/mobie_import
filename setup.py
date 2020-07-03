 # -*- coding: utf-8 -*-

from distutils.core import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='bdv_tools',
      version='20200703',
      py_modules=['bdv_tools','submit_slurm'],
      description='Tools to interact with BigDataViewer.',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='Martin Schorb',
      author_email='schorb@embl.de',
      license='GPLv3',
      install_requires=[
      'numpy'
      ],
      ) 
