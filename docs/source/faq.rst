.. _faq:

Frequently Asked Questions
==========================

How can I include a ``github`` repository in a lab Project
----------------------------------------------------------

Like ``pip``, lab works with ``requirements.txt`` file. To let lab know that your virtual environment should contain a package maintained on github, add the following line to your ``requirements.txt``:

.. code::

  -e git+https://github.com/beringresearch/ivis#egg=ivis

Modify repository and package information accordingly.
