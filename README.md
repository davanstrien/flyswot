# flyswot

[![PyPI](https://img.shields.io/pypi/v/flyswot.svg)][pypi_]
[![Status](https://img.shields.io/pypi/status/flyswot.svg)][status]
[![Python Version](https://img.shields.io/pypi/pyversions/flyswot)][python version]
[![License](https://img.shields.io/pypi/l/flyswot)][license]

[![Read the documentation at https://flyswot.readthedocs.io/](https://img.shields.io/readthedocs/flyswot/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/davanstrien/flyswot/actions/workflows/tests.yml/badge.svg)](https://github.com/davanstrien/flyswot/actions/workflows/tests.yml)
[![Codecov](https://codecov.io/gh/davanstrien/flyswot/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi_]: https://pypi.org/project/flyswot/
[status]: https://pypi.org/project/flyswot/
[python version]: https://pypi.org/project/flyswot
[license]: https://opensource.org/licenses/MIT
[read the docs]: https://flyswot.readthedocs.io/
[tests]: https://github.com/davanstrien/flyswot/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/davanstrien/flyswot
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

![flyswot logo](https://raw.githubusercontent.com/davanstrien/flyswot/main/docs/_static/fly.png?token=ACEUI5KJ2HPO4ZGNTBX6OE3ARMXII)

## Disclaimer 😬

_flyswot_ is a work in progress. Things may not work and behaviour may change in the future!

## tl;dr

_flyswot_ is a Command Line Tool which allows you to run [Hugging Face Transformers](https://huggingface.co/docs/transformers/) [image classification models](https://huggingface.co/models?pipeline_tag=image-classification&sort=downloads) available via the [Hugging Face Hub](https://huggingface.co/models) 🤗 against a directory of images. It returns a CSV report containing the models predictions.

```console
flyswot predict directory image_directory csv_reports --model_id flyswot/convnext-tiny-224_flyswot
```

## Features

Currently _flyswot_ supports:

- 🚀 automatic downloading of models from the Hugging Face Hub
- 🔎 UNIX style search patterns for matching images to predict against
- 📸 filtering by image extension
- 📜 a CSV output report containing the paths to the input images, the predicted label and the models confidence for that prediction.
- 📊 a summary 'report' on the command line providing a high level summary of the predictions made by `flyswot`

[![asciicast](https://asciinema.org/a/449685.svg)](https://asciinema.org/a/449685)

## Why?

What is the point of this? Why not just write a Python script? This seems like a terrible idea...

_flyswot_ was originally for a project with the [Heritage Made Digital](https://www.bl.uk/projects/heritage-made-digital) team at the [British Library](https://www.bl.uk). In this project we wanted to detect 'fake flysheets'. We designed how _flyswot_ works with this particular use case in mind.

There are a few main reasons why we decided a command line tool was the best approaches to utilising the models we were developing.

- The digitised images we are working with can be very large
- The images we are working with are often subject to copyright
- Inference speed isn't a big priority

Since we're using computer vision for _assisting_ rather than _automation_ we felt a CLI was a useful interface for interacting with the models.

## Installation

You can install _flyswot_ via [pip] from [PyPI]:

```console
$ pip install flyswot
```

This will install the latest release version of _flyswot_

## Detailed Installation Guide

[Installation] provides a more detailed guide to installing _flyswot_. This more detailed guide is aimed at users of _flyswot_ who may be less familiar with Python.

## Usage

You can see help for _flyswot_ using `flyswot --help`

<!-- [[[cog
import cog
from flyswot.cli import app
from typer.testing import CliRunner
runner = CliRunner()
result = runner.invoke(app, ["--help"])
help = result.output.replace("Usage: root", "Usage: flyswot")
cog.out(
    "```\n{}\n```".format(help)
)
]]] -->

```
Usage: flyswot [OPTIONS] COMMAND [ARGS]...

Options:
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.

Commands:
  model    flyswot commands for interacting with models
  predict  flyswot commands for making predictions

```

<!-- [[[end]]] -->

### Making predictions

You can get help for the prediction functionality for _flyswot_ as follows:

<!-- [[[cog
import cog
from flyswot.cli import app
from typer.testing import CliRunner
runner = CliRunner()
result = runner.invoke(app,  ["predict", "directory", "--help"])
help = result.output.replace("Usage: root", "Usage: flyswot")
cog.out(
    "```\n{}\n```".format(help)
)
]]] -->

```
Usage: flyswot predict directory [OPTIONS] DIRECTORY CSV_SAVE_DIR

  Predicts against all images stored under DIRECTORY which match PATTERN in the
  filename.

  By default searches for filenames containing 'fs'.

  Creates a CSV report saved to `csv_save_dir`

Arguments:
  DIRECTORY     Directory to start searching for images from  [required]
  CSV_SAVE_DIR  Directory used to store the csv report  [required]

Options:
  --model-id TEXT       The model flyswot should use for making predictions
                        [default: flyswot/convnext-tiny-224_flyswot]
  --pattern TEXT        Pattern used to filter image filenames  [default: fs]
  --bs INTEGER          Batch Size  [default: 16]
  --image-formats TEXT  Image format(s) to check  [default: .tif]
  --help                Show this message and exit.

```

<!-- [[[end]]] -->

To run predictions against a directory of images:

```console
$ flyswot predict directory manuscripts_folder .
```

- _flyswot_ will search inside the manuscripts_folder looking for image files.
- By default it will look for files that contain `FS` in the filename since these are files which have been labelled as being "end flysheets" or "front flysheets"
- Once it has found all the files labelled as `flysheet` it will then run a computer vision model against these images to see if they are labelled correctly i.e. if it is indeed a flysheet or something else.
- _flyswot_ will save a csv report containing the paths to the image, the directory the image is stored in, the label, and the confidence for that prediction.

#### Changing the model

You can also tell _flyswot_ to use a different image classification model via the `model-id` parameter. For example to use the [microsoft/dit-base-finetuned-rvlcdip](https://huggingface.co/microsoft/dit-base-finetuned-rvlcdip) model we could run:

```console
flyswot predict directory Documents/DS/hugit-cli/fs Desktop/ --model-id microsoft/dit-base-finetuned-rvlcdip

```

This will download the latest available version of this model from the Hugging Face Hub and predict against the specified filenames. **Note** under the hood _flyswot_ uses the Hugging Face [transformers](https://huggingface.co/docs/transformers/) [pipelines](https://huggingface.co/docs/transformers/pipeline_tutorial) for inference. The model you specific must therefore be compatible with this pipeline.

## Detailed Usage Guide

This section provides additional guidance on the usage of _flyswot_. This is primarily aimed at [HMD](https://www.bl.uk/projects/heritage-made-digital) users of _flyswot_.

### How flyswot searches for images

_flyswot_ is currently intended to identify images which have an incorrect label associated with them. In particular it is currently intended to identify "fake" flysheets. These images have `fs` as part of their filename so we can tell _flyswot_ to use this pattern in the filename to identify images which should be checked using the computer vision model. This can be changed if you also want to match other filename patterns.

Since these images of concern will often be inside a directory structure _flyswot_ will look in sub-folders from the input folder for images which contain `fs` in the name. For example in the following folder structure:

```console
Collection/
├─ item1/
│  ├─ add_ms_9403_fbspi.tif
│  ├─ add_ms_9403_fse001r.tif
│  ├─ add_ms_9403_fse001v.tif
├─ item2/
│  ├─ sloane_ms_116_fblefr.tif
│  ├─ sloane_ms_116_fbspi.tif
│  ├─ sloane_ms_116_fse004r.tif
```

All of the files which have `fs` in the filname will be check but files which don't contains `fs` such as `add_ms_9403_fbspi.tif` will be ignored since these aren't labelled as flysheets.

### Running flyswot against a directory of images

To run _flyswot_ against a directory of images you need to give it the path to that directory/folder.
There are different ways you could do this. The following is suggested for people who are not very familiar (yet 😜) with terminal interfaces.

Identify the folder you want to _flyswot_ to check for "fake" flysheets. If you are using _flyswot_ for the first time it may make sense to choose a folder which doesn't contain a huge number of collection items so you don't have to wait to long for _flyswot_ to finish running. Once you have found a directory you want to predict against copy the path. This path should be the full path to the item.

For example something that looks like:

```console
\\ad\collections\hmd\excitingcollection\excitingsubcollection\
```

This will be the folder from which _flyswot_ starts looking.

When you activated your conda environment in a terminal, you were likely 'inside' your user directory. Since we need to specify a place for _flyswot_ to store the CSV report, we'll move to a better place to store that output; your `Desktop` folder. To do we can navigate using the command:

```console
$ chdir desktop
```

if you are using Mac, Linux or have GitBash installed you should instead run:

```console
$ cd Desktop
```

This will take you to your Desktop. We'll now run _flyswot_. As with many other command line tools, _flyswot_ has commands and sub-commands. We are interested in the `predict` command. This includes two sub-commands: `predict-image` and `directory`. We will mostly want to predict directories. To do this we use the following approach

```console
$ flyswot predict directory input_directory output_directory
```

The input directory is the folder containing our images and the output directory is where we want to save our CSV report. Using the folder we previously identified this would look like:

```console
$ flyswot predict directory "\\ad\collections\hmd\excitingcollection\excitingsubcollection\" .
```

We can use `.` to indicate we want the CSV report to be saved to the current directory (in this case the Deskop directory). Also notice that there are quotation marks `""` around the path. This is used to make sure that any spaces in the path are escaped.

Once you run this command you should see some progress reported by _flyswot_, including a progress bar that shows how many of the images _flyswot_ has predicted against.

When _flyswot_ has finshed you will have a CSV 'report' which contains the path to the image, the predicted label and the confidence for that prediction.

## License

Distributed under the terms of the [MIT license],
_flyswot_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [@cjolowicz]'s [Hypermodern Python Cookiecutter] template.

[@cjolowicz]: https://github.com/cjolowicz
[cookiecutter]: https://github.com/audreyr/cookiecutter
[mit license]: https://opensource.org/licenses/MIT
[pypi]: https://pypi.org/
[hypermodern python cookiecutter]: https://github.com/cjolowicz/cookiecutter-hypermodern-python
[file an issue]: https://github.com/davanstrien/flyswot/issues
[pip]: https://pip.pypa.io/
[installation]: https://flyswot.readthedocs.io/en/latest/installation.html

<!-- github-only -->

[contributor guide]: https://github.com/davanstrien/flyswot/blob/main/CONTRIBUTING.md
[background]: https://flyswot.readthedocs.io/en/latest/background.html
