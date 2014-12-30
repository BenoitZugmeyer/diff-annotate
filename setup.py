# -*- coding: utf-8 -*-
from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='diff-annotate',
      version='0.0.1',
      description='Format a diff by adding annotations',
      long_description=readme(),
      url='https://github.com/BenoitZugmeyer/diff-annotate/',
      author='Benoît Zugmeyer',
      author_email='bzugmeyer@gmail.com',
      license='Expat',
      packages=['diff_annotate'],
      install_requires=[
          'click >=3.3, <4',
          'docutils >=0.12, <1',
          'pygments >=2.0.1, <3',
      ],
      entry_points={
          'console_scripts': ['diff-annotate=diff_annotate:main'],
      },
      zip_safe=True)
