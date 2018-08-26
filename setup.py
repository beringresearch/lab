''' pip install --editable . '''
from setuptools import setup

setup(
    name="lab",
    version="0.5.0",
    py_modules=['lab'],
    install_requires=[
        'click',
        'pyyaml',
        'sklearn'
        ],
    entry_points='''
    [console_scripts]
    lab=lab.cli:cli
    '''
    )
