# Machine Learning Lab
Command line interface for the management of arbitrary machine learning tasks.

# Installation
```
git clone https://github.com/beringresearch/lab
cd lab
pip install --editable .
```

# Creating a new Lab Project
```
lab init --name [NAME] --r requirements.txt
```

# Concepts
Lab employs several concepts: __hyperparameter logging__, __performance metrics__, and __model persistence__.
A typical machine learning workflow can be truned into a Lab Experiment by using a single decorator.

# Example

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

from lab.sklearn import Experiment

e = Experiment()

@e.start_run
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

    e.log_metric('accuracy_score', accuracy)
    e.log_metric('precision_score', precision)

    e.log_parameter('C', C)
    e.log_parameter('gamma', gamma)

    e.log_model(clf, 'svm')
```

# Running a project
Lab Project can be initialised through:

```
lab run <PATH/TO/TRAIN.py>
```

This creates a `.labrun` folder with artificats of the run.

# Comparing models
From the directory that contains `.labrun`, execute:

```
lab ls
```

The output stacks existing models and allows comparisons across logged performance metrics.