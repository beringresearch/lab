.. _quickstart:

Quickstart
==========

Installing Lab
--------------

For the time being, lab is available through our github repository:

.. code-block:: bash

    git clone https://github.com/beringresearch/lab
    cd lab
    pip install --editable .

.. note::

    You cannot install Lab on the MacOS system installation of Python. We recommend installing
    Python 3 through the `Homebrew <https://brew.sh/>`_ package manager using
    ``brew install python``.

Setting up your first Project
-----------------------------
Lab projects are initiated using a ``requirements.txt`` file. This ensures a consistent and reproducible environment.

Let's create a simple environment that imports sklearn:

.. code-block:: bash

    echo "sklearn" >> requirements.txt
    lab init --name test

Lab will run through project initialisation and create a new **test** project with its own virtual environment.

Creating your first Lab Experiment
----------------------------------
Training scripts can be placed directly into the *test/* directory. Here's an example training script, *train.py*, set up to train a Random Forest classifier with appropriate Lab logging API:

.. code-block:: python

    from sklearn import datasets
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score

    from lab.experiment import Experiment # Import Experiment

    e = Experiment() # Initialise Lab Experiment

    @e.start_run # Indicate the start of the Experiment
    def train():        
        iris = datasets.load_iris()
        X = iris.data
        y = iris.target

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.24, random_state=42)
        
        n_estimators = 100

        e.log_features(['Sepal Length', 'Sepal Width', 'Petal Length', 'Petal Width'])
        clf = RandomForestClassifier(n_estimators = n_estimators)
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average = 'macro')

        e.log_metric('accuracy_score', accuracy)        # Log accuracy
        e.log_metric('precision_score', precision)      # Log aprecision

        e.log_parameter('n_estimators', n_estimators)   # Log parameters of your choice

        e.log_model('randomforest', clf)                # Log the actual model

Running a Lab Experiment
------------------------

The Experiment can now be launched through:

.. code-block:: bash

    lab run train.py

Lab will log performance metrics and model files into appropriate Experiment folders.

Compare Lab Experiments
------------------------

Multiple Experiments can be compared from the root of the Project folder:

.. code-block:: bash

    lab ls

    Experiment    Source              Date        accuracy_score    precision_score
    ------------  ------------------  ----------  ----------------  -----------------
    49ffb76e      train_mnist_mlp.py  2019-01-15  0.97: ██████████  0.97: ██████████
    261a34e4      train_mnist_cnn.py  2019-01-15  0.98: ██████████  0.98: ██████████