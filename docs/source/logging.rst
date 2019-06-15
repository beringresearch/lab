.. _logging:

Tracking Machine Learning Experiments 
=====================================

The Lab logging component was designed to interface directly with your training code without disrupting the machine learning workflow.
Currently, users can keep track of the following experiment artfacts:

- ``e.log_features``: Feature names
- ``e.log_parameter``: Hyperparameters
- ``e.log_metric``: Performance metrics
- ``e.log_artifact``: Experimental artifacts
- ``e.log_model``: Model persistence

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

    # Initialize Lab Experiment
    @e.start_run
    def train():
        iris = datasets.load_iris()
        feature_names = iris['feature_names']
        
        # Log features
        e.log_features(feature_names)

Hyperparameters: ``e.log_parameter``
-------------------------------------

Let's carry on with the Iris dataset and consider a Random Forest Classifier with an exhaustive grid search along the number of trees and maximum depth of a tree:

.. code-block:: python

    from sklearn import datasets
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import GridSearchCV
    from lab.experiment import Experiment #import lab Experiment
    
    e = Experiment()

    # Initialize Lab Experiment
    @e.start_run
    def train():
        iris = datasets.load_iris()

        feature_names = iris['feature_names']

        # Log features
        e.log_features(feature_names)
        
        parameters = {'n_estimators': [10, 50, 100],
                      'max_depth': [2, 4]}
        
        rfc = RandomForestClassifier()

        # Run a grid search
        clf = GridSearchCV(rfc, parameters)
        clf.fit(iris.data, iris.target)

        best_parameters = clf.best_estimator_.get_params()

        # Log parameters
        e.log_parameter('n_estimators', best_parameters['n_estimators'])
        e.log_parameter('max_depth', best_parameters['max_depth'])

Performance Metrics: ``e.log_metric``
-------------------------------------

Lab was designed to easily compare multiple machine lerning experiments through consistent performance metrics.
Let's expand our example and assess model accuracy and precision.

.. code-block:: python

    from sklearn import datasets
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import GridSearchCV
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score
    from lab.experiment import Experiment 
    
    e = Experiment()

    # Initialize Lab Experiment
    @e.start_run
    def train():
        iris = datasets.load_iris()

        feature_names = iris['feature_names']

        # Log features
        e.log_features(feature_names) 
        
        parameters = {'n_estimators': [10, 50, 100],
                      'max_depth': [2, 4]}
        
        # Run a grid search 
        rfc = RandomForestClassifier()
        clf = GridSearchCV(rfc, parameters)
        clf.fit(iris.data, iris.target)

        best_parameters = clf.best_estimator_.get_params()

        # Log parameters
        e.log_parameter('n_estimators', best_parameters['n_estimators'])
        e.log_parameter('max_depth', best_parameters['max_depth'])

        X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target,
                                                test_size=0.25, random_state=42)

        rfc = RandomForestClassifer(n_estimators = best_parameters['n_estimators'],
                                    max_depth = best_parameters['max_depth'])
        rfc.fit(X_train, y_train)

        # Generate predictions
        y_pred = rfc.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)                           
        precision = precision_score(y_test, y_pred, average = 'macro')      

        # Log performance metrics
        e.log_metric('accuracy_score', accuracy)
        e.log_metric('precision_score', precision) 

Experiment Artifacts: ``e.log_artifact``
----------------------------------------

In certain cases, it may be desirable for a Lab Experiment to write certain artifacts to a temporary folder - e.g.
ROC curves or Tensorboard log directory. Lab naturally bundles these artifacts within each respective experiment for subsequent exploration.

Let's explore an example where Lab logs Tensorboard outputs:

.. code-block:: python

    # Additional imports would go here
    from keras.callbacks import TensorBoard
    import tempfile
    
    from lab.experiment import Experiment

    e = Experiment()
   
    @e.start_run
    def train():
    
      # ... Further training code goes here

      # Create a temporary directory for tensorboard logs
      output_dir = dirpath = tempfile.mkdtemp()
      print("Writing TensorBoard events locally to %s\n" % output_dir)
    
      tensorboard = TensorBoard(log_dir=output_dir)

      model.fit(x_train, y_train,
                batch_size=batch_size,
                epochs=epochs,
                verbose=1,
                validation_data=(x_test, y_test),
                callbacks=[tensorboard])

      # Log tensorboard artifact
      e.log_artifact('tensorboard', output_dir)


In this example, Tensorboard logs are written to a temporary folder, which can be tracked in real-time. Once the run is complete,
Lab moves all the directory content into a subdirectory of the current Lab Experiment.


Model Persistence: ``e.log_model``
----------------------------------

Finally, it's useful to store model objects themselves for future use. Consider our fitted GridSearchCV object ``clf`` from an earlier example.
It can now be logged using a simple expression:

.. code-block:: python

    e.log_model('GridSearchCV', clf)
