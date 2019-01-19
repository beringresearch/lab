import imp
import os
from setuptools import setup

version = imp.load_source(
    'lab.version', os.path.join('lab', 'version.py')).VERSION

setup(
    name="lab",
    version=version,
    py_modules=['lab'],
    install_requires=[
        'click>=6.7',
        'minio',
        'numpy',
        'pandas',
        'pyyaml',
        'scikit-learn',        
        'tabulate'
        ],
    entry_points='''
    [console_scripts]
    lab=lab.cli:cli
    ''',
    author='Bering',
    description='Lab: a command line interface for the management of arbitrary machine learning tasks.',
    license='Apache License 2.0',
    classifiers=[
        'Intended Audience :: Developers',        
        'Programming Language :: Python :: 3.6',
    ],
    keywords='ml ai',
    url='https://beringresearch.com'
    )
