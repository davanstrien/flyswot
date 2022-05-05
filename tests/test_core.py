"""Tests for core module."""
import os
import typing
from pathlib import Path
from typing import Any
from typing import List

import pytest
from hypothesis import strategies  # type: ignore
from hypothesis.core import given  # type: ignore

from flyswot import core

# flake8: noqa
# mypy: allow-untyped-defs

int_values = strategies.integers()
str_values = strategies.text()

patterns_to_test: List[str] = [
    "fse",
    "fbspi",
    "Rblefr",
    "fblefv",
    "fs001r",
    "fs001v",
    "f001r",
    "f001v",
    "f197ar",
    "f197br",
    "fse002av",
    "fse002bv",
    "fbrigr",
    "fbrigv",
]


@pytest.fixture(scope="session", params=patterns_to_test)
def image_files_pattern(tmpdir_factory, fname):
    """Fixture for image file patterns"""
    a_dir = tmpdir_factory.mktemp("image_dir")
    for number in range(2000):
        file = a_dir.join(f"file_{fname}_{number}.tif")
        file.ensure()
        file2 = a_dir.join(f"file_{number}.jpg")
        file2.ensure()
    return a_dir


@pytest.mark.parametrize("fname", patterns_to_test)
def test_filter(fname, tmpdir):
    """It filters files from pattern"""
    a_dir = tmpdir.mkdir("image_dir")
    for number in range(50):
        file = a_dir.join(f"file_{fname}_{number}.tif")
        file.ensure()
        file2 = a_dir.join(f"file_{number}.jpg")
        file2.ensure()
    for i in range(5):  # create 25 files in 5 subfolders
        a_sub_dir = a_dir.mkdir(f"{i}_dir")
        for i in range(5):
            file = a_sub_dir.join(f"file_{fname}_{i}.tif")
            file.ensure()
    matches = core.get_image_files_from_pattern(a_dir, fname, ".tif")
    files = [f for f in Path(a_dir).rglob("**/*") if f.is_file()]
    assert len(files) == (50 * 2) + 25
    assert len(list(matches)) == 50 + 25


patterns_to_test_with_front: List[str] = [
    "fs",
    "fse",
    "fbspi",
    "Rblefr",
    "fblefv",
    "fs001r",
    "fs001v",
    "f001r",
    "f001v",
    "f197ar",
    "f197br",
    "fse002av",
    "fse002bv",
    "fbrigr",
    "fbrigv",
]

image_extensions = ["tif", "tiff", "jpg", "jpeg", "png"]


@pytest.mark.parametrize("ext", image_extensions)
def test_get_all_images(ext, tmpdir):
    """It gets all image files"""
    a_dir = tmpdir.mkdir("image_dir")
    for number in range(50):
        file = a_dir.join(f"file_{number}.{ext}")
        file.ensure()
    for i in range(5):  # create 25 files in 5 subfolders
        a_sub_dir = a_dir.mkdir(f"{i}_dir")
        for i in range(5):
            file = a_sub_dir.join(f"file_{i}.{ext}")
            file.ensure()
    matches = core.get_image_files_from_pattern(a_dir, None, None)
    files = [f for f in Path(a_dir).rglob("**/*") if f.is_file()]
    assert len(files) == 50 + 25
    assert len(list(matches)) == 50 + 25  # all image files matched


@pytest.mark.parametrize("pattern", patterns_to_test)
def test_get_all_images_with_pattern(pattern, tmpdir):
    """It gets all image files"""
    image_extensions = ["tif", "tiff", "jpg", "jpeg", "png"]
    a_dir = tmpdir.mkdir("image_dir")
    for number in range(2):
        for ext in image_extensions:
            file = a_dir.join(f"file{pattern}_{number}.{ext}")
            file.ensure()
    for ext in image_extensions:
        matches = core.get_image_files_from_pattern(a_dir, None, ext)
        files = [f for f in Path(a_dir).rglob(f"**/{ext}") if f.is_file()]
        assert len(list(matches)) == 2

    matches = core.get_image_files_from_pattern(a_dir, pattern, None)
    files = [f for f in Path(a_dir).rglob("**/*") if f.is_file()]
    assert len(files) == 2 * len(image_extensions)
    assert len(list(matches)) == 2 * len(image_extensions)  # all image files matched


def test_count_files_with_extension(tmpdir):
    a_dir = tmpdir.mkdir("image_dir")
    for number in range(50):
        file = a_dir.join(f"file_{number}.tif")
        file.ensure()
    count = core.count_files_with_ext(a_dir, ".tif")
    assert count == 50


@pytest.mark.parametrize("fname", patterns_to_test_with_front)
def test_filter_with_front(fname, tmpdir):
    """It filters files from pattern"""
    a_dir = tmpdir.mkdir("image_dir")
    for number in range(50):
        file = a_dir.join(f"file_{fname}_{number}.tif")
        file.ensure()
        file2 = a_dir.join(f"file_{number}.jpg")
        file2.ensure()
    for i in range(5):  # create 25 files in 5 subfolders
        a_sub_dir = a_dir.mkdir(f"{i}_dir")
        for i in range(5):
            file = a_sub_dir.join(f"file_{fname}_{i}.tif")
            file.ensure()
    matches = core.get_image_files_from_pattern(a_dir, fname, ".tif")
    files = [f for f in Path(a_dir).rglob("**/*") if f.is_file()]
    assert len(files) == (50 * 2) + 25
    assert len(list(matches)) == 50 + 25


@pytest.mark.parametrize("fname", patterns_to_test)
def test_filter_matching_files(fname, tmp_path):
    """It filters files from pattern when file in both extensions"""
    a_dir = tmp_path / "image_dir"
    a_dir.mkdir()
    for number in range(50):
        file = a_dir / f"file_{fname}_{number}.tif"
        file.touch()
        file2 = a_dir / f"file_{fname}_{number}.jpg"
        file2.touch()
    files = Path(a_dir).rglob("**/*")
    files = (file for file in files if file.suffix in [".jpg", ".tif"])
    matches = core.filter_to_preferred_ext(
        files,
        [".tif"],
    )
    files = [f for f in Path(a_dir).rglob("**/*") if f.is_file()]
    assert len(files) == 100
    print(matches)
    assert len(list(matches)) == 50


@pytest.fixture()
def image_files(tmpdir_factory):
    """Fixture for image files"""
    a_dir = tmpdir_factory.mktemp("image_dir")
    for fname in range(2000):
        file = a_dir.join(f"file_{fname}.tif")
        file.ensure()
    for fname in range(1000):
        file = a_dir.join(f"file_{fname}.jpg")
        file.ensure()
    return a_dir


def test_filter_to_preferred_ext(image_files):
    """It filters to preferred extension"""
    tiff_files = list(Path(image_files).glob("*.tif"))
    assert len(tiff_files) == 2000
    jpeg_files = list(Path(image_files).glob("*.jpg"))
    assert len(jpeg_files) == 1000
    image_files = list(Path(image_files).iterdir())
    return_files = list(core.filter_to_preferred_ext(image_files, [".jpg"]))
    assert len(return_files) == 2000


@pytest.mark.parametrize("fname", patterns_to_test)
def test_filter_matching_files_in_different_directories(fname, tmp_path):
    """It filters files from pattern when file live in different directories"""
    img_dir = tmp_path / "image_dir"
    img_dir.mkdir()
    tif_dir = img_dir / "tif"
    tif_dir.mkdir()
    jpg_dir = img_dir / "jpg"
    jpg_dir.mkdir()
    for number in range(50):
        file = tif_dir / f"file_{fname}_{number}.tif"
        file.touch()
        file2 = jpg_dir / f"file_{fname}_{number}.jpg"
        file2.touch()
    files = Path(img_dir).rglob("**/*")
    files = (file for file in files if file.suffix in [".jpg", ".tif"])
    matches = core.filter_to_preferred_ext(
        files,
        [".tif"],
    )
    files = [
        f
        for f in Path(img_dir).rglob("**/*")
        if f.is_file() and not f.name.startswith(".")
    ]
    assert len(files) == 100
    assert len(list(matches)) == 50


@given(strategies.lists(int_values, min_size=1))
def test_signal_last(l):
    """It returns last element in list when `is"""
    *_, last = l
    for is_last_element, var in core.signal_last(l):
        if is_last_element:
            assert var == last


def test_signal_last_raises_value_error_with_no_length():
    """It raises value error when no length"""
    with pytest.raises(ValueError):
        items: List[Any] = []
        for i in core.signal_last(items):
            print(i)


@given(
    strategies.dictionaries(
        keys=strategies.text(min_size=1), values=strategies.integers(), min_size=1
    )
)
def test_signal_last_dictionary(d):
    """It returns last element for dictionary"""
    *_, last = d
    for is_last_element, var in core.signal_last(d.items()):
        if is_last_element:
            key, value = var
            assert key == last


@given(
    strategies.dictionaries(
        keys=strategies.text(min_size=1), values=strategies.integers(), min_size=1
    )
)
def test_signal_last_truth(d):
    """It returns True for last element"""
    dict_len = len(d)
    for i, (is_last_element, var) in enumerate(core.signal_last(d.items()), start=1):
        if i != dict_len:
            assert is_last_element == False
        if i == dict_len:
            assert is_last_element == True
