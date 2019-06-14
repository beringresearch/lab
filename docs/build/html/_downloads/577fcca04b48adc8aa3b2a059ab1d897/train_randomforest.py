"""
Getting started with Lab and scikit-learn
=========================================

This example illustrates how Lab can be used to create and run a simple
classifier on the iris dataset.

Begin by creating a new Lab Project:

    >>> echo "scikit-learn" > requirements.txt
    >>> lab init --name simple-iris

"""

import argparse
from sklearn import datasets
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score

from lab.experiment import Experiment

parser = argparse.ArgumentParser('Test arguments')

parser.add_argument('--n_estimators', type=int, dest='n_estimators')
args = parser.parse_args()

n_estimators=args.n_estimators

if n_estimators is None:
    n_estimators=100
    max_depth=2

if __name__ == "__main__":
    e = Experiment(dataset='iris_75')

    @e.start_run
    def train():
        iris = datasets.load_iris()
        X = iris.data
        y = iris.target

        X_train, X_test, y_train, y_test = train_test_split(X, y,
                                                            test_size=0.25,
                                                            random_state=42)

        e.log_features(['Sepal Length', 'Sepal Width', 'Petal Length',
                        'Petal Width'])
        clf = RandomForestClassifier(n_estimators=n_estimators)

        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average = 'macro')

        e.log_metric('accuracy_score', accuracy)
        e.log_metric('precision_score', precision)

        e.log_parameter('n_estimators', n_estimators)
        e.log_parameter('max_depth', max_depth)

        e.log_model('randomforest', clf)

##############################################################
# After execute training script through the `lab run` command.
#
# >>> lab run train.py
# >>> lab ls
