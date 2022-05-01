"""Tests model module."""
import datetime
import time
from pathlib import Path
from typing import Any
from typing import Dict

import click
import onnxruntime as ort
import pytest
import rich
import typer
from huggingface_hub import hf_api
from typer.testing import CliRunner
from typing_extensions import runtime

from flyswot import models
from flyswot.models import app
from flyswot.models import ensure_model_dir
from flyswot.models import load_vocab
from flyswot.models import vocab

runner = CliRunner()


# flake8: noqa


def test_app_exists() -> None:
    """It exists"""
    assert models.app


def test_url_callback() -> None:
    url_latest = "latest"
    assert models._url_callback(url_latest) == url_latest
    valid_url = "https://google.com"
    assert models._url_callback(valid_url) == valid_url
    with pytest.raises(typer.BadParameter):
        bad_url = "nope"
        models._url_callback(bad_url)


def test_ensure_model_dir_returns_path(tmp_path: Any) -> None:
    """It returns paths"""
    model_dir_path = tmp_path / "app"
    model_dir_path.mkdir()
    model_dir = models.ensure_model_dir(model_dir_path)
    assert model_dir.exists()
    assert model_dir.is_dir()
    assert model_dir.absolute().parts[-1] == "models"


def test_show_model_dir() -> None:
    result = runner.invoke(app, ["show-model-dir"])
    assert result.exit_code == 0
    assert "model" in result.stdout


def test_local_model(tmp_path: Any) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir(parents=True)
    assert model_dir.is_dir()
    vocab = model_dir / "vocab.txt"
    vocab.touch()
    model_card = model_dir / "README.md"
    model_card.touch()
    modelfile = model_dir / "20210331.onnx"
    modelfile.touch()
    parts = models.LocalModel(model_dir)
    assert parts.vocab
    assert parts.model
    assert parts.modelcard


def test_ensure_model() -> None:
    model_dir = ensure_model_dir()
    model_parts = models.ensure_model(model_dir)
    assert model_parts


def test_load_vocab() -> None:
    vocab = models.load_vocab(Path("tests/test_files/test_vocab.txt"))
    assert vocab
    assert type(vocab) == list
    assert type(vocab[0]) == list


def test_vocab_raises() -> None:
    with pytest.raises(NotImplementedError):
        models.vocab(model="not_latest")


def test_vocab() -> None:
    vocab = models.vocab(model="latest", show=False)
    assert vocab
    assert isinstance(vocab, list)


def test_vocab_print(capsys) -> None:
    models.vocab(model="latest", show=True)
    captured = capsys.readouterr()
    assert len(captured.out) > 2
    assert "Model Vocab" in captured.out


def test_show_model_card(tmp_path):
    model_dir = tmp_path / "model"
    model_dir.mkdir(parents=True)
    assert model_dir.is_dir()
    vocab = model_dir / "vocab.txt"
    vocab.touch()
    model_card = model_dir / "README.md"
    model_card.touch()
    modelfile = model_dir / "20210331.onnx"
    modelfile.touch()
    localmodel = models.LocalModel(model_dir)
    models.show_model_card(localmodel)


def test_app(tmp_path: Any) -> None:
    pass


def test_create_metrics_tables():
    model_info = hf_api.model_info("flyswot/convnext-tiny-224_flyswot")
    metric_table = models.create_metrics_tables(model_info)
    assert metric_table
    assert isinstance(metric_table, list)
    assert isinstance(metric_table[0], rich.table.Table)


def test_create_model_card():
    card = models.create_markdown_model_card("flyswot/convnext-tiny-224_flyswot")
    assert card
    assert isinstance(card, rich.markdown.Markdown)


def test_model_card_link():
    link = models.hub_model_link("flyswot/convnext-tiny-224_flyswot")
    assert link
    assert isinstance(link, str)
