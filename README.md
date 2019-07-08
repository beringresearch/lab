[![Documentation Status](https://readthedocs.org/projects/bering-ml-lab/badge/?version=latest)](https://bering-ml-lab.readthedocs.io/en/latest/?badge=latest)

# Machine Learning Lab

A lightweight command line interface for the management of arbitrary machine learning tasks.

Documentation is available at: <https://bering-ml-lab.readthedocs.io/en/latest/>

NOTE: Lab is in active development - expect a bumpy ride!

![alt text](https://github.com/beringresearch/lab/blob/master/docs/source/_static/lab_screenshot.jpeg "Bering's Lab")

## Installation

The latest stable version can be installed directly from PyPi:

```bash
pip install lab-ml
```

Development version can be installed from github.

```bash
git clone https://github.com/beringresearch/lab
cd lab
pip install --editable .
```

## Concepts

Lab employs three concepts: __reproducible environment__, __logging__, and __model persistence__.
A typical machine learning workflow can be turned into a Lab Experiment by adding a single decorator.

## Creating a new Lab Project

```bash
lab init --name [NAME]
```

Lab will look for a **requirements.txt** file in the working directory to generate a portable virtual environment for ML experiments.

## Setting up a Lab Experiment

Here's a simple script that trains an SVM classifier on the iris data set:

```python
from sklearn import svm, datasets
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score

C = 1.0
gamma = 0.7
iris = datasets.load_iris()
X = iris.data
y = iris.target

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.24, random_state=42)

clf = svm.SVC(C, 'rbf', gamma=gamma, probability=True)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, average = 'macro')
```

It's trivial to create a Lab Experiment using a simple decorator:

```python
from sklearn import svm, datasets
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score

from lab.experiment import Experiment ## New Line

e = Experiment() ## New Line

@e.start_run ## New Line
def train():
    C = 1.0
    gamma = 0.7
    iris = datasets.load_iris()
    X = iris.data
    y = iris.target

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.24, random_state=42)

    clf = svm.SVC(C, 'rbf', gamma=gamma, probability=True)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average = 'macro')

    e.log_metric('accuracy_score', accuracy) ## New Line
    e.log_metric('precision_score', precision) ## New Line

    e.log_parameter('C', C) ## New Line
    e.log_parameter('gamma', gamma) ## New Line

    e.log_model('svm', clf) ## New Line
```

## Running an Experiment

Lab Experiments can be run as:

```bash
lab run <PATH/TO/TRAIN.py>
```

## Comparing models

Lab assumes that all Experiments associated with a Project log consistent performance metrics. We can quickly assess performance of each experiment by running:

```bash
lab ls

Experiment    Source              Date        accuracy_score    precision_score
------------  ------------------  ----------  ----------------  -----------------
49ffb76e      train_mnist_mlp.py  2019-01-15  0.97: ██████████  0.97: ██████████
261a34e4      train_mnist_cnn.py  2019-01-15  0.98: ██████████  0.98: ██████████
```

## Pushing models to a centralised repository

Lab experiments can be pushed to a centralised filesystem through integration with [minio](https://minio.io). Lab assumes that you have setup minio on a private cloud.

Lab can be configured once to interface with a remote minio instance:

```bash
lab config minio --tag my-minio --endpoint [URL:PORT] --accesskey [STRING] --secretkey [STRING]
```

To push a local lab experiment to minio:

```bash
lab push --tag my-minio --bucket [BUCKETNAME] .
```

Copyright 2019, Bering Limited
