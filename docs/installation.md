# Installing flyswot

flyswot supports Python 3.8 and higher. To install flyswot from pip run:

```console
pip install flyswot

```

Since `flyswot` is a command line application it is a good candiate for install via [pipx](https://pypa.github.io/pipx/).

```console
pipx install flyswot
```

## Detailed Installation Guide

This section gives a more detailed instructions for installing _flyswot_. This guidance is aimed particularly at [HMD](https://www.bl.uk/projects/heritage-made-digital) users of _flyswot_. This set of instructions covers the steps required to install _flyswot_.

### Note on the examples

You will see examples for input in the guidance below which looks like:

```console
$ pip
```

The `$` symbol here is often used as a convention to show that this is input to a terminal/command line. When you input this into your own terminal you should only input the part after the `$` symbol. For example, in the above case you would type `pip`.

### Install Python

_flyswot_ uses the [Python](https://www.python.org/) programming language. You will therefore need to have Python installed on your computer to run _flyswot_.

For HMD users of `flyswot` it is suggested to use the [Anaconda](https://www.anaconda.com/) distribution of Python. If you are on a managed PC/laptop you should request this to be installed via the Technology team.

### Create and activate a Conda Environment

A virtual environment allows us to isolate the requirements of different python packages. This can be useful since different python packages might have different requirements. Using a virtual environment allows us to install these in a way where you are less likely to have conflicts between these packages.

There are various different ways of creating virtual environments within Python. Anaconda comes with a system for creating virtual environment's. Creating Conda environments within Conda can be done in various ways, if you are new to Python and Anaconda it is suggested to use [Anaconda Navigator](https://docs.anaconda.com/anaconda/navigator/index.html).

You can find more detailed instructions for creating a new virtual environments in the [Anaconda documentation](https://docs.anaconda.com/). Briefly you should:

- Open Anaconda Navigator
- Navigate to the _Environments_ tab
- Create a new Python environment and give it a descriptive name i.e. _flyswot_. You should ensure that the Python version is version 3.8 or above.

Once you have created this new environment you can "activate it" by clicking on the arrow next to the name of the environment. You should select the "open terminal". This should open a new terminal window. On the left you should see the name of your environment in brackets:

```console
(flyswot) $
```

### Install flyswot in your Conda Environment

Now you have created and activated your conda environment you can install flyswot. Before doing this you can check that [pip] is available inside your environment:

```console
$ pip
```

This should return the help pages for [pip]. We can now use [pip] to install _flyswot_ from [PyPI].
To do this run:

```console
$ pip install flyswot
```

You should now see the installation process begin. During this you will see some information printed to the terminal abou what packages are being installed.

### Check flyswot is installed

We can quickly confirm that _flyswot_ has been installed by printing out the help information. We can do this by typing:

```console
$ flyswot --help
```

This should print some help information to the screen. If you get this it means you have successfully installed _flyswot_ 💪.

### Update flyswot

If you need to upgrade your version of flyswot you should activate your Conda Environment and then run

```console
$ pip install flyswot --upgrade
```
