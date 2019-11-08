from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='lab-ml',
    version='0.81.89.dev',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    py_modules=['lab'],
    install_requires=[
        'click>=6.7',
        'minio',
        'numpy',
        'pandas',
        'pyyaml',
        'tabulate',
        'graphviz',
        'joblib'
        ],
    entry_points='''
    [console_scripts]
    lab=lab.cli:cli
    ''',
    author='Ignat Drozdov',
    author_email='idrozdov@beringresearch.com',
    description='Lab: a command line interface for the management of arbitrary machine learning tasks.',
    license='Apache License 2.0',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
    ],
    keywords='ml ai',
    url='https://github.com/beringresearch/lab'
    )
