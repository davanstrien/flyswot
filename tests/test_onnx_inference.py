#!/usr/bin/env python3
import csv
import inspect
import os
import pathlib
import shutil
import string
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import rich
import typer
from hypothesis import given
from hypothesis import strategies
from hypothesis import strategies as st
from hypothesis.core import given
from toolz import itertoolz

from flyswot import onnx_inference

# flake8: noqa

text_strategy = st.text(string.ascii_letters, min_size=1)

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "test_files",
)


def test_onnx_session_attributes():
    session = onnx_inference.OnnxInferenceSession(
        Path("tests/test_files/mult/20210629/model/2021-06-29-model.onnx"),
        Path("tests/test_files/mult/20210629/model/vocab.txt"),
    )
    assert session
    assert inspect.ismethod(session.predict_image)
    assert inspect.ismethod(session.predict_batch)
    assert inspect.ismethod(session._postprocess)
    assert inspect.ismethod(session._load_image)


def test_softmax():
    scores = [3.0, 1.0, 0.2]
    scores = np.array(scores)
    data = np.array([[10, 20, 40], [1, 4, 3]])
    output = onnx_inference.softmax(data)
    assert output is not None
    assert isinstance(output, np.ndarray)
    output = onnx_inference.softmax(scores)
    assert np.isclose(output, np.array([0.8360188, 0.11314284, 0.05083836])).all()
