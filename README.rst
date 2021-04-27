flyswot
=======

|PyPI| |Python Version| |License|

|Read the Docs| |Tests| |Codecov|

|pre-commit| |Black|

.. |PyPI| image:: https://img.shields.io/pypi/v/flyswot.svg
   :target: https://pypi.org/project/flyswot/
   :alt: PyPI
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/flyswot
   :target: https://pypi.org/project/flyswot
   :alt: Python Version
.. |License| image:: https://img.shields.io/pypi/l/flyswot
   :target: https://opensource.org/licenses/MIT
   :alt: License
.. |Read the Docs| image:: https://img.shields.io/readthedocs/flyswot/latest.svg?label=Read%20the%20Docs
   :target: https://flyswot.readthedocs.io/
   :alt: Read the documentation at https://flyswot.readthedocs.io/
.. |Tests| image:: https://github.com/davanstrien/flyswot/workflows/Tests/badge.svg
   :target: https://github.com/davanstrien/flyswot/actions?workflow=Tests
   :alt: Tests
.. |Codecov| image:: https://codecov.io/gh/davanstrien/flyswot/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/davanstrien/flyswot
   :alt: Codecov
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. |Black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black

.. image:: https://raw.githubusercontent.com/davanstrien/flyswot/main/docs/_static/fly.png?token=ACEUI5KJ2HPO4ZGNTBX6OE3ARMXII


Disclaimer
-----------

`flyswot` is a work in progress and is currently only intended to be used for testing.

Features
--------

`flyswot` is a Command Line Tool for detecting 'fake' flysheets. TODO add description of project

* unix style search patterns for matching images to predict against
* produces a csv output containing the paths to the input images, the predicted label and the models confidence for that prediction.


Requirements
------------

* Python 3.7+


Installation
------------

You can install *flyswot* via pip_ from PyPI_:

.. code:: console

   $ pip install flyswot


Even better, if you have pipx:

.. code:: console

   $ pipx install flyswot


Usage
-----

To run predictions against a directory of images:

.. code:: console

   $ flyswot predict directory manuscripts_folder .

- :code:`flyswot` will search inside the :code:`manuscripts_folder` looking for image files.
- By default it will look for files that contain :code:`FSE` in the filename since these are files which have been labelled as being "end flysheets".
- Once it has found all the files labelled as `flysheet` it will then run a computer vision model against these images to see if they are labbeled correctly i.e. if it is indeed a flysheet or something else.
- flyswot will save a csv report containing the paths to the image, the directory the image is stored in, the label, and the confidence for that prediction.


Contributing
------------

Contributions are very welcome.
To learn more, see the `Contributor Guide`_.


License
-------

Distributed under the terms of the `MIT license`_,
*flyswot* is free and open source software.


Issues
------

If you encounter any problems,
please `file an issue`_ along with a detailed description.


Credits
-------


This project was generated from `@cjolowicz`_'s `Hypermodern Python Cookiecutter`_ template.

.. _@cjolowicz: https://github.com/cjolowicz
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _MIT license: https://opensource.org/licenses/MIT
.. _PyPI: https://pypi.org/
.. _Hypermodern Python Cookiecutter: https://github.com/cjolowicz/cookiecutter-hypermodern-python
.. _file an issue: https://github.com/davanstrien/flyswot/issues
.. _pip: https://pip.pypa.io/
.. github-only
.. _Contributor Guide: CONTRIBUTING.rst
.. _Usage: https://flyswot.readthedocs.io/en/latest/usage.html
