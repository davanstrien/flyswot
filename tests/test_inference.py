import csv
import os
import pathlib
from typing import Any

import pytest
import typer
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.core import given

from flyswot import inference

# flake8: noqa


def test__image_predicton_item_raises_error_when_too_few_params():
    """It raises Typerror when passed too few items"""
    with pytest.raises(TypeError):
        item = inference.ImagePredictionItem("A")


def test_image_prediction_items_match(tmp_path):
    im_path = tmp_path / "image.tif"
    label = "flysheet"
    confidence = 0.9
    item = inference.ImagePredictionItem(im_path, label, confidence)
    assert item.path == im_path
    assert item.predicted_label == "flysheet"
    assert item.confidence == 0.9
    assert type(item.path) == pathlib.PosixPath or pathlib.WindowsPath
    assert type(item.confidence) == float


@pytest.fixture(scope="session")
def imfile(tmpdir_factory):
    image_dir = tmpdir_factory.mktemp("images")
    imfile = image_dir.join("image1.tif")
    imfile.ensure()
    return imfile


@given(confidence=st.floats(max_value=100.0), label=st.text(min_size=1))
def test_image_prediction_item(confidence, label, imfile: Any):
    item = inference.ImagePredictionItem(imfile, label, confidence)
    assert item.path == imfile
    assert item.predicted_label == label
    assert item.confidence == confidence
    assert type(item.confidence) == float


@given(confidence=st.floats(max_value=100.0), label=st.text(min_size=1))
def test_prediction_batch(confidence: float, label: str, imfile: Any):
    item = inference.ImagePredictionItem(imfile, label, confidence)
    item2 = inference.ImagePredictionItem(imfile, label, confidence)
    batch = inference.PredictionBatch([item, item2])
    assert batch.batch_labels
    assert len(list(batch.batch_labels)) == 2
    assert hasattr(batch.batch_labels, "__next__")


FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "test_files",
)


@pytest.mark.datafiles(
    os.path.join(
        FIXTURE_DIR,
        "fly_fse.jpg",
    )
)
def test_predict_directory(datafiles, tmp_path) -> None:
    inference.predict_directory(
        datafiles, tmp_path, pattern="fse", bs=1, image_format=".jpg"
    )
    csv_file = list(tmp_path.rglob("*.csv"))
    assert csv_file
    with open(csv_file[0], newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            assert row["path"]
            assert row["directory"]
            assert row["predicted_label"]
            assert row["confidence"]
            assert type(float(row["confidence"])) == float


def test_predict_empty_directory(tmp_path) -> None:
    test_dir = tmp_path / "test"
    test_dir.mkdir()
    with pytest.raises(typer.Exit):
        inference.predict_directory(test_dir)
