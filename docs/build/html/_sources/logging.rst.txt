.. _logging:

Logging Experiment Artifacts
============================

The Lab logging component was designed to interface directly with your training code without disrupting the machine learning workflow.
Currently, users can keep track of the following experiment artfacts:

- Feature names
- Hyperparameters
- Performance metrics
- Model files

Feature names
-------------
Data features are simply lists of feature names or column indices. Consider the snippet:

.. code-block:: python

    from sklearn import datasets
    
    iris = datasets.load_iris()
    feature_names = iris['feature_names']

    print(feature_names)

    ['sepal length (cm)',
     'sepal width (cm)',
     'petal length (cm)',
     'petal width (cm)']

We can log these features by adding a few lines of code:

.. code-block:: python

    from sklearn import datasets
    from lab.experiment import Experiment #import lab Experiment
    
    e = Experiment()
    e.start_run()                         # Initiate an experiment
    def train():
        iris = datasets.load_iris()
        feature_names = iris['feature_names']

        e.log_features(feature_names)     # Log features

Hyperparameters
---------------

Let's carry on with the Iris dataset and consider a Random Forest Classifier with an exhaustive grid search along the number of trees and maximum depth of a tree:

.. code-block:: python

    from sklearn import datasets
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import GridSearchCV
    from lab.experiment import Experiment #import lab Experiment
    
    e = Experiment()
    e.start_run()                         # Initiate an experiment
    def train():
        iris = datasets.load_iris()

        feature_names = iris['feature_names']
        e.log_features(feature_names)     # Log features
        
        parameters = {'n_estimators': [10, 50, 100],
                      'max_depth': [2, 4]}
        
        rfc = RandomForestClassifier()
        clf = GridSearchCV(rfc, parameters)
        clf.fit(iris.data, iris.target)

        best_parameters = clf.best_estimator_.get_params()

        e.log_parameter('n_estimators', best_parameters['n_estimators'])
        e.log_parameter('max_depth', best_parameters['max_depth'])

Performance Metrics
-------------------

Lab was designed to easily compare multiple machine lerning experiments through consistent performance metrics.
Let's expand our example and assess model accuracy and precision.

.. code-block:: python

    from sklearn import datasets
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import GridSearchCV
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score
    from lab.experiment import Experiment #import lab Experiment
    
    e = Experiment()
    e.start_run()                         # Initiate an experiment
    def train():
        iris = datasets.load_iris()

        feature_names = iris['feature_names']
        e.log_features(feature_names)     # Log features
        
        parameters = {'n_estimators': [10, 50, 100],
                      'max_depth': [2, 4]}
        
        rfc = RandomForestClassifier()
        clf = GridSearchCV(rfc, parameters)
        clf.fit(iris.data, iris.target)

        best_parameters = clf.best_estimator_.get_params()

        e.log_parameter('n_estimators', best_parameters['n_estimators'])
        e.log_parameter('max_depth', best_parameters['max_depth'])

        X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target,
                                                test_size=0.25, random_state=42)

        rfc = RandomForestClassifer(n_estimators = best_parameters['n_estimators'],
                                    max_depth = best_parameters['max_depth'])
        rfc.fit(X_train, y_train)

        y_pred = rfc.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)                           
        precision = precision_score(y_test, y_pred, average = 'macro')      

        e.log_metric('accuracy_score', accuracy)    # Log accuracy    
        e.log_metric('precision_score', precision)  # Log precisions

Model Artifacts
---------------

Finally, it's useful to store model objects themselves for future use. Consider our fitted GridSearchCV object ``clf`` from an earlier example.
It can now be logged using a simple expression:

.. code-block:: python

    e.log_model('GridSearchCV', clf)