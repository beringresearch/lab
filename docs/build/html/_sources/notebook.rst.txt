.. _notebook:

Working with Jupyter Notebooks
==============================

Lab makes it easy to launch a jupyter notebook directly inside the lab Project:

.. code-block:: bash

    lab notebook

The operation launches Jupyter Lab and creates a project-specific kernel, tying it directly to the Lab virtual environment.

To switch from Jupyter Lab to Jupyter Notebook, simply pass a --notebook flag:

.. code-block:: bash

    lab notebook --notebook
