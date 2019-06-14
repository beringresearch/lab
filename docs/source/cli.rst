.. _cli:

======================
Command Line Interface
======================

Lab is invoked through a simple Command Line Interface (CLI).

.. code::
    
    lab --help

    Usage: lab [OPTIONS] COMMAND [ARGS]...

    Bering's Machine Learning Lab

    Copyright 2019 Bering Limited. https://beringresearch.com

    Options:
    --help  Show this message and exit.

    Commands:
      config    Global Lab configuration
      info      Display system-wide information
      init      Initialise a new Lab Project
      ls        Compare multiple Lab Experiments
      notebook  Launch a jupyter notebook
      pull      Pulls Lab Experiment from minio to current...
      push      Push Lab Experiment to minio
      rm        Remove a Lab Experiment
      run       Run a training script
      show      Show a Lab Experiment
      update    Update Lab Environment from Project's... 


General Parameters
------------------

``config`` ``minio``
^^^^^^^^^^^^^^^^^^^^

Setup remote minio host

.. code::

  Usage: lab config minio [OPTIONS]

  Setup remote minio host

  Options:
    --tag TEXT        helpful minio host tag  [required]
    --endpoint TEXT   minio endpoint address  [required]
    --accesskey TEXT  minio access key  [required]
    --secretkey TEXT  minio secret key  [required]
    --help            Show this message and exit.

`tag` option is a helpful name to identify a minio endpoint. It can be used to quickly access push and pull APIs.

``info``
^^^^^^^^

Display system-wide information, including Lab version, number of CPUs, etc.

.. code::

  Usage: lab info [OPTIONS]

Project
-------

``init``
^^^^^^^^

Initialise a new Lab Project.

.. code::

  Usage: lab init [OPTIONS] 

  Options:
    --name TEXT  environment name
    --help       Show this message and exit.

Command is run in the presence of a ``requirements.txt`` file that describes the Project environment. Lab will create a dedicate virtual environemnt in a ``.venv`` directory.

``ls``
^^^^^^

List Lab Experiments and their performance metrics.

.. code::

  Usage: lab ls [OPTIONS] [SORT_BY]

  Options:
    --help  Show this message and exit.

Optional ``SORT_BY`` option is a string column name in the results table. For example, if a Lab Experiment logged a metric AUC, calling ``lab ls AUC`` sort all Experiments by decreasing AUC values. The default is to show the most recently completed Lab run.

``show``
^^^^^^^^

Create a PNG file of experiment-data-script-hyperparameter-performance diagram.

.. code::

  Usage: lab show

  Options:
    --help  Show this message and exit.

``notebook``
^^^^^^^^^^^^
Lancuhes a jupyter notebook, pointing to the ``notebooks`` directory. If this is the first time launching the notebook, Lab will automatically create a jupyter kernel using the ``requirements.txt`` file. Kernel name is stored on your system as TIMESTAMP_PROJECT_NAME.

``update``
^^^^^^^^^^
Updates the Lab project. Can be run if the local Lab version was updated or if ``requirements.txt`` has been modified with additional dependencies.

Experiment
----------

``run``
^^^^^^^
Execute a Lab Experiment.

.. code::

  Usage: lab run [OPTIONS] [SCRIPT]... 

  Options:
    --help  Show this message and exit.

``rm``
^^^^^^

Remove a Lab Experiment

.. code::

  Usage: lab rm [OPTIONS] EXPERIMENT_ID
 
EXPERIMENT_ID can be obtained by running ``lab ls`` inside the Project directory.

Model Management
----------------

``push``
^^^^^^^^

Push Lab Project to a configured minio repository.

.. code::
  
  lab push --tag [MINIO_TAG] --bucket [TEXT] .


``pull``
^^^^^^^^

Pull a Lab Project from a configured minio repository.

.. code::

  lab pull --tag [MINIO_TAG] --bucket [TEXT] --project [TEXT].
