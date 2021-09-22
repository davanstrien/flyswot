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

*flyswot* is a work in progress and is currently only intended to be used for testing by `HMD`_.

Features
--------

`flyswot` is a Command Line Tool for detecting 'fake' flysheets. TODO add description of project

* unix style search patterns for matching images to predict against
* produces a csv output containing the paths to the input images, the predicted label and the models confidence for that prediction.

Requirements
------------

* Python 3.7 or greater

TODO update this section with requirements and uses.

Installation
------------

You can install *flyswot* via pip_ from PyPI_:

.. code:: console

   $ pip install flyswot

This will install the latest release version of *flyswot*

Detailed Installation Guide
---------------------------

This section gives a more detailed instructions for installing *flyswot*. This guidance is aimed particularly at `HMD`_ users of *flyswot*. This set of instructions covers the steps required to install *flyswot*.

Note on the examples
^^^^^^^^^^^^^^^^^^^^

You will see examples for input in the guidance below which looks like:

.. code:: console

          $ pip

The ``$`` symbol here is often used as a convention to show that this is input to a terminal/command line. When you input this into your own terminal you should only input the part after the ``$`` symbol. For example, in the above case you would type ``pip``.


Install Python
^^^^^^^^^^^^^^

*flyswot* uses the `Python`_ programming language. You will therefore need to have Python installed on your computer to run *flyswot*.

For HMD users of `flyswot` it is suggested to use the `Anaconda`_ distribution of Python. If you are on a managed PC/laptop you should request this via Technology.

Create and activate a Conda Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A virtual environment allows us to isolate the requirements of different python packages. This can be useful since different python packages might have different requirements. Using a virtual environment allows us to install these in a way where you are less likely to have conflicts between these packages.

There are various different ways of creating virtual environments within Python. Anaconda comes with a system for creating virtual environment's. Creating Conda environments within Conda can be done in various ways, if you are new to Python and Anaconda it is suggested to use `Anaconda Navigator`_.

You can find more detailed instructions for creating a new virtual environments in the `Anaconda documentation`_. Briefly you should:

- Open Anaconda Navigator
- Navigate to the *Environments* tab
- Create a new Python environment and give it a descriptive name i.e. *flyswot*. You should ensure that the Python version is version 3.7 or above.

Once you have created this new environment you can "activate it" by clicking on the arrow next to the name of the environment. You should select the "open terminal". This should open a new terminal window. On the left you should see the name of your environment in brackets:

.. code:: console

    (flyswot) $

Install flyswot in your Conda Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now you have created and activated your conda environment you can install flyswot. Before doing this you can check that `pip`_ is available inside your environment:

.. code:: console

          $ pip

This should return the help pages for `pip`_. We can now use `pip`_ to install *flyswot* from `PyPI`_.
To do this run:

.. code:: console

   $ pip install flyswot

You should now see the installation process begin. During this you will see some information printed to the terminal abou what packages are being installed.

Check flyswot is installed
^^^^^^^^^^^^^^^^^^^^^^^^^^

We can quickly confirm that *flyswot* has been installed by printing out the help information. We can do this by typing:

.. code:: console

  $ flyswot --help

This should print some help information to the screen. If you get this it means you have successfully installed *flyswot* 💪.

Update flyswot
^^^^^^^^^^^^^^^

If you need to upgrade your version of flyswot you should activate your Conda Environment and then run

.. code:: console

   $ pip install flyswot --upgrade


Usage
-----

To run predictions against a directory of images:

.. code:: console

   $ flyswot predict directory manuscripts_folder .

- *flyswot* will search inside the manuscripts_folder looking for image files.
- By default it will look for files that contain :code:`FS` in the filename since these are files which have been labelled as being "end flysheets" or "front flysheets"
- Once it has found all the files labelled as `flysheet` it will then run a computer vision model against these images to see if they are labelled correctly i.e. if it is indeed a flysheet or something else.
- flyswot will save a csv report containing the paths to the image, the directory the image is stored in, the label, and the confidence for that prediction.

Detailed Usage Guide
--------------------

This section provides additional guidance on the usage of *flyswot*. This is primarily aimed at `HMD`_ users of *flyswot*.

How flyswot searches for images
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*flyswot* is currently intended to identify images which have an incorrect label associated with them. In particular it is currently intended to identify "fake" flysheets. These images have ``fs`` as part of their filename so this is used by flyswot to identify images which should be checked using the computer vision model. This can be channged if you also want to match other filename patterns.

Since these images of concern will often be inside a directory structure *flyswot* will look in sub-folders from the input folder for images which contain ``fs`` in the name. For example in the following folder structure:

.. code:: console

   Collection/
   ├─ item1/
   │  ├─ add_ms_9403_fbspi.tif
   │  ├─ add_ms_9403_fse001r.tif
   │  ├─ add_ms_9403_fse001v.tif
   ├─ item2/
   │  ├─ sloane_ms_116_fblefr.tif
   │  ├─ sloane_ms_116_fbspi.tif
   │  ├─ sloane_ms_116_fse004r.tif



Running flyswot against a directory of images
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run *flyswot* against a directory of images you need to give it the path to that directory/folder.
There are different ways you could do this. The following is suggested for people who are not very familiar (yet 😜) with terminal interfaces.

Identify the folder you want to flyswot to check for "fake" flysheets. If you are using *flyswot* for the first time it may make sense to choose a folder which doesn't contain a huge number of collection items so you don't have to wait to long for *flyswot* to finish running. Once you have found a directory you want to predict against copy the path. This path should be the full path to the item.

For example something that looks like:

.. code:: console

  \\ad\collections\hmd\excitingcollection\excitingsubcollection\


This will be the folder from which *flyswot* starts looking.

When you activated your conda environment in a terminal, you were likely 'inside' your user directory. Since we need to specify a place for *flyswot* to store the CSV report, we'll move to a better place to store that output; your ``Desktop`` folder. To do we can navigate using the command:

.. code:: console

   $ chdir desktop


if you are using  Mac, Linux or have GitBash installed you should instead run:

.. code:: console

   $ cd Desktop



This will take you to your Desktop. We'll now run *flyswot*. As with many other command line tools, *flyswot* has commands and sub-commands. We are interested in the ``predict`` command. This includes two sub-commands: ``predict-image`` and ``directory``.  We will mostly want to predict directories. To do this we use the following approach

.. code:: console

   $ flyswot predict directory input_directory output_directory

The input directory is the folder containing our images and the output directory is where we want to save our CSV report. Using the folder we previously identified this would look like:

.. code:: console

   $ flyswot predict directory "\\ad\collections\hmd\excitingcollection\excitingsubcollection\" .

We can use ``.`` to indicate we want the CSV report to be saved to the current directory (in this case the Deskop directory). Also notice that there are quotation marks ``""`` around the path. This is used to make sure that any spaces in the path are escaped.

Once you run this command you should see some progress reported by *flyswot*, including a progress bar that shows how many of the images *flyswot* has predicted against.

When *flyswot* has finshed you will have a CSV 'report' which contains the path to the image, the predicted label and the confidence for that prediction.


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
.. _HMD: https://www.bl.uk/projects/heritage-made-digital
.. _Python: https://www.python.org/
.. _Anaconda: https://www.anaconda.com/products/individual
.. _Anaconda Navigator: https://docs.anaconda.com/anaconda/navigator/
.. _Anaconda Documentation: https://docs.anaconda.com/anaconda/navigator/tutorials/manage-environments/#creating-a-new-environment
