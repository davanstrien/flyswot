import csv
import os
import pathlib
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest
import rich
import typer
from hypothesis import given
from hypothesis import strategies
from hypothesis import strategies as st
from hypothesis.core import given
from rich.table import Column
from toolz import itertoolz

from flyswot import inference

# flake8: noqa


def test__image_prediction_item_raises_error_when_too_few_params():
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
def test_multi_image_prediction_item(confidence, label, imfile: Any):
    item = inference.MultiLabelImagePredictionItem(
        imfile, [(label, confidence), (label, confidence)]
    )
    assert item.path == imfile
    assert type(item.predictions) == list
    assert type(item.predictions[0]) == tuple
    assert item.predictions[0][0] == label
    assert item.predictions[1][0] == label
    assert item.predictions[0][1] == confidence
    assert item.predictions[1][1] == confidence


@given(confidence=st.floats(max_value=100.0), label=st.text(min_size=1))
def test_prediction_batch(confidence: float, label: str, imfile: Any):
    item = inference.ImagePredictionItem(imfile, label, confidence)
    item2 = inference.ImagePredictionItem(imfile, label, confidence)
    batch = inference.PredictionBatch([item, item2])
    assert batch.batch_labels
    assert len(list(batch.batch_labels)) == 2
    assert hasattr(batch.batch_labels, "__next__")


@given(confidence=st.floats(min_value=0.0, max_value=100.0), label=st.text(min_size=1))
def test_multi_prediction_batch(confidence: float, label: str, imfile: Any):
    item = inference.MultiLabelImagePredictionItem(
        imfile, [(label, confidence), (label, confidence)]
    )
    item2 = inference.MultiLabelImagePredictionItem(
        imfile, [(label, confidence), (label, confidence)]
    )
    batch = inference.MultiPredictionBatch([item, item2])
    assert batch.batch
    assert type(batch.batch) == list
    assert type(batch.batch[0]) == inference.MultiLabelImagePredictionItem
    assert batch.batch_labels
    assert len(list(batch.batch_labels)) == 2
    assert hasattr(batch.batch_labels, "__next__")
    for labels in batch.batch_labels:
        for label in labels:
            assert label == label


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
        datafiles,
        tmp_path,
        pattern="fse",
        bs=1,
        image_format=".jpg",
        model_name="latest",
    )
    csv_file = list(tmp_path.rglob("*.csv"))
    assert csv_file
    with open(csv_file[0], newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            assert row["path"]
            assert row["directory"]
        columns = defaultdict(list)
    with open(csv_file[0], newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            for (k, v) in row.items():
                columns[k].append(v)
        assert any("prediction" in k for k in columns)
        labels = [columns[k] for k in columns if "prediction" in k]
        confidences = [columns[k] for k in columns if "confidence" in k]
        # check all labels are strings
        assert all(map(lambda x: isinstance(x, str), (itertoolz.concat(labels))))
        # check all confidences can be cast to float
        assert all(
            map(
                lambda x: isinstance(x, float),
                map(lambda x: float(x), (itertoolz.concat(confidences))),
            )
        )


def test_csv_header():
    with pytest.raises(NotImplementedError):
        inference.create_csv_header("string", Path("."))


def test_csv_header_multi(tmp_path):
    predicton = inference.MultiLabelImagePredictionItem(Path("."), [("label", 0.8)])
    batch = inference.MultiPredictionBatch([predicton, predicton])
    csv_fname = tmp_path / "test.csv"
    inference.create_csv_header(batch, csv_fname)
    with open(csv_fname, "r") as f:
        reader = csv.DictReader(f)
        list_of_column_names = [header for header in reader.fieldnames]
    assert "path" in list_of_column_names
    assert "directory" in list_of_column_names


def test_csv_header_single(tmp_path):
    predicton = inference.ImagePredictionItem(Path("."), "label", 0.6)
    batch = inference.PredictionBatch([predicton])
    csv_fname = tmp_path / "test.csv"
    inference.create_csv_header(batch, csv_fname)
    with open(csv_fname, "r") as f:
        reader = csv.DictReader(f)
        list_of_column_names = [header for header in reader.fieldnames]
    assert "path" in list_of_column_names
    assert "directory" in list_of_column_names
    assert "confidence" in list_of_column_names


@given(strategies.lists(st.text(min_size=2), min_size=2), st.text())
def test_print_table(labels, title):
    table = inference.print_table(labels, title, print=False)
    assert isinstance(table, rich.table.Table)
    assert table.title == title
    unique = itertoolz.count(itertoolz.unique(labels))
    assert table.row_count == unique + 1
    assert all(
        label in getattr(itertoolz.first(table.columns), "_cells") for label in labels
    )


@given(strategies.lists(st.text(), min_size=1))
def test_check_files(l):
    inference.check_files(l, "fse", Path("."))


def test_check_files_emopty():
    with pytest.raises(typer.Exit):
        inference.check_files([], "fse", Path("."))


def test_make_layout():
    layout = inference.make_layout()
    assert layout
    assert isinstance(layout, rich.layout.Layout)


# def test_predict_empty_directory(tmp_path) -> None:
#     test_dir = tmp_path / "test"
#     test_dir.mkdir()
#     with pytest.raises(typer.Exit):
#         inference.predict_directory(test_dir)
