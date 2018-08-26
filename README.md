# Machine Learning Lab
Command line interface for the management of arbitrary machine learning tasks.

# Installation
```
git clone https://github.com/beringresearch/lab
cd lab
virtualenv -p python3 lab
pip install --editable .
```

# Example

|Script to train an SVM on the iris dataset                   | The same script as a Lab experiment                         |
|-------------------------------------------------------------|-------------------------------------------------------------|
|`python`                                                     |`python                                                      |
|`from sklearn import svm, datasets`                          |`from sklearn import svm, datasets`                          |
|`from sklearn.model_selection import train_test_split`       |`from sklearn.model_selection import train_test_split`       |
|`from sklearn.metrics import accuracy_score, precision_score`|`from sklearn.metrics import accuracy_score, precision_score`|
|` `                                                          |``                                                           |
|` `                                                          |`from lab.sklearn import Experment                           |
|` `                                                          |` `                                                          |
|` `                                                          |`e = Experiment()`                                           |
|` `                                                          |``                                                           |
|` `                                                          |`@e.start_run`                                               |
|` `                                                          |`def run():`                                                 |
|`C = 1.0`                                                    |`    C = 1.0`                                                |
|`gamma = 0.7`                                                |`    gamma = 0.7`                                            |
|`iris = datasets.load_iris()`                                |`    iris = datasets.load_iris()`                            |
|`X = iris.data`                                              |`    X = iris.data`                                          |
|`y = iris.target`                                            |`    y = iris.target`                                        |
|``                                                           |` `                                                          |
|`X_train, X_test, y_train, y_test = \\`                      |`    X_train, X_test, y_train, y_test = \\`                  |
|`   train_test_split(X, y, test_size=0.24, random_state=42)` |`    train_test_split(X, y, test_size=0.24, random_state=42)`|
|``                                                           |``                                                           |   
|``                                                           |``                                                           |
|`clf = svm.SVC(C, 'rbf', gamma=gamma, probability=True)`     |`    clf = svm.SVC(C, 'rbf', gamma=gamma, probability=True)` |
|`clf.fit(X_train, y_train)`                                  |`c   lf.fit(X_train, y_train)`                               |
|``                                                           |``                                                           |
|`y_pred = clf.predict(X_test)`                               |`    y_pred = clf.predict(X_test)`                           |
|`accuracy = accuracy_score(y_test, y_pred)`                  |`    accuracy = accuracy_score(y_test, y_pred)`              |
|`precision = precision_score(y_test, y_pred, \\`             |`    precision = precision_score(y_test, y_pred, \\`         |
|`   average = 'macro')`                                      |`    average = 'macro')`                                     |
|``                                                           |``                                                           |
|``                                                           |`    e.log_metric('accuracy_score', accuracy)`               |
|``                                                           |`    e.log_metric('precision_score', precision)`             |
|``                                                           |``                                                           |
|``                                                           |`    e.log_parameter('C', C)`                                |
|``                                                           |`    e.log_parameter('gamma', gamma)`                        |
|``                                                           |``                                                           |   
|``                                                           |`    e.log_model(clf, 'svm')`                                |