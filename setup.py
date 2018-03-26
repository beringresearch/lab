''' pip install --editable . '''
from setuptools import setup

setup(
    name="lab",
    version="0.3.0",
    py_modules=['lab'],
    install_requires=[
        'click',
        'tabulate',
        'pandas', 
        'pymongo'
    ],
    entry_points='''
    [console_scripts]
    lab=lab.cli:cli
    '''
    )
