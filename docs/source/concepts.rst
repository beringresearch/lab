.. _concepts:

Concepts
========

Lab is centred around three core concepts: *Reproducibility*, *Logging*, and *Model Persistence*. Lab is designed to integrate with your existing
training scripts, with imposing as few constraints as possible. 


Reproducibility
---------------

Lab Projects are designed to be shared and re-used. This feature makes havy use of Python's ``virtualenv`` module,
enabling users to precisely define modules and environments that are required to run the associated experiments.

Every Project is initiated using a `requirements.txt <https://pip.readthedocs.io/en/1.1/requirements.html>`_ file.

Logging
-------

Lab was designed to benchmark multiple predictive models and hyperparameters. To accomplish this, it implements a simple API that stores:

- Feature names
- Hyperparameters
- Performance metrics
- Model files

Model Persistence
-----------------

Models are logged using the ``pickle`` module. This applies to both ``sklearn`` and ``keras`` experiments. This simple structure allows for a quick
performance assessment and deployment of a model of choice into production.

Example Use Cases
-----------------

At Bering, we use Lab for a number of use cases:

**Data Scientists** track individual experiments locally on their machine, consistently organising all files and artefacts for reproducibility.
By setting up a naming schema, Teams can work together on the same datasets to benchmark performance of novel ML algorithms.

**Production Engineers** assess model performances and decide on the best possible model to be served in production environments. Lab's strict model
versioning serves as a link between research and development environment and evolving production components.

**ML Researchers** can publish code to GitHub as a Lab Project, making it easy for others to reproduce findings.