''' pip install --editable . '''
from setuptools import setup

setup(
    name="lab",
    version="0.5.5",
    py_modules=['lab'],
    install_requires=[
        'click',
        'numpy',
        'pandas',
        'pyyaml',
        'sklearn',
        'flask',
        'tabulate'
        ],
    entry_points='''
    [console_scripts]
    lab=lab.cli:cli
    '''
    )
