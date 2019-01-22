.. _cli:

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
        config  Configure the lab environment and setup...
        init    Initialise a new Lab environment
        ls      Compare multiple Lab Experiments
        push    Push lab experiment to minio
        run     Run a training script

Each individual command has a detailed help screen accessible via ``lab command_name --help``.