from setuptools import setup

setup(
        name = "lab",
        version = "0.1",
        py_modules=['lab'],
        install_requires=[
            'Click',
            'terminaltables',
            'pymongo' 
        ],
        entry_points='''
        [console_scripts]
        lab=lab.cli:cli
        '''
        )
