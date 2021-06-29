"""Tests model module."""
import datetime
import time
from pathlib import Path
from typing import Any
from typing import Dict

import click
import onnxruntime as ort
import pytest
import typer
from typer.testing import CliRunner
from typing_extensions import runtime

from flyswot import models
from flyswot.models import app
from flyswot.models import ensure_model_dir
from flyswot.models import load_vocab

runner = CliRunner()


# flake8: noqa


def test_app_exists() -> None:
    """It exists"""
    assert models.app


single_github_release_dict: Dict[Any, Any] = {
    "url": "https://api.github.com/repos/davanstrien/learn-onnx/releases/40756746",
    "assets_url": "https://api.github.com/repos/davanstrien/learn-onnx/releases/40756746/assets",
    "upload_url": "https://uploads.github.com/repos/davanstrien/learn-onnx/releases/40756746/assets{?name,label}",
    "html_url": "https://github.com/davanstrien/learn-onnx/releases/tag/2021.03.31",
    "id": 40756746,
    "author": {
        "login": "davanstrien",
        "id": 8995957,
        "node_id": "MDQ6VXNlcjg5OTU5NTc=",
        "avatar_url": "https://avatars.githubusercontent.com/u/8995957?v=4",
        "gravatar_id": "",
        "url": "https://api.github.com/users/davanstrien",
        "html_url": "https://github.com/davanstrien",
        "followers_url": "https://api.github.com/users/davanstrien/followers",
        "following_url": "https://api.github.com/users/davanstrien/following{/other_user}",
        "gists_url": "https://api.github.com/users/davanstrien/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/davanstrien/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/davanstrien/subscriptions",
        "organizations_url": "https://api.github.com/users/davanstrien/orgs",
        "repos_url": "https://api.github.com/users/davanstrien/repos",
        "events_url": "https://api.github.com/users/davanstrien/events{/privacy}",
        "received_events_url": "https://api.github.com/users/davanstrien/received_events",
        "type": "User",
        "site_admin": False,
    },
    "node_id": "MDc6UmVsZWFzZTQwNzU2NzQ2",
    "tag_name": "2021.03.31",
    "target_commitish": "main",
    "name": "2021.03.31",
    "draft": False,
    "prerelease": False,
    "created_at": "2021-03-28T18:33:30Z",
    "published_at": "2021-03-31T12:47:12Z",
    "assets": [
        {
            "url": "https://api.github.com/repos/davanstrien/learn-onnx/releases/assets/34258568",
            "id": 34258568,
            "node_id": "MDEyOlJlbGVhc2VBc3NldDM0MjU4NTY4",
            "name": "2021-03-31-model.onnx",
            "label": None,
            "uploader": {
                "login": "davanstrien",
                "id": 8995957,
                "node_id": "MDQ6VXNlcjg5OTU5NTc=",
                "avatar_url": "https://avatars.githubusercontent.com/u/8995957?v=4",
                "gravatar_id": "",
                "url": "https://api.github.com/users/davanstrien",
                "html_url": "https://github.com/davanstrien",
                "followers_url": "https://api.github.com/users/davanstrien/followers",
                "following_url": "https://api.github.com/users/davanstrien/following{/other_user}",
                "gists_url": "https://api.github.com/users/davanstrien/gists{/gist_id}",
                "starred_url": "https://api.github.com/users/davanstrien/starred{/owner}{/repo}",
                "subscriptions_url": "https://api.github.com/users/davanstrien/subscriptions",
                "organizations_url": "https://api.github.com/users/davanstrien/orgs",
                "repos_url": "https://api.github.com/users/davanstrien/repos",
                "events_url": "https://api.github.com/users/davanstrien/events{/privacy}",
                "received_events_url": "https://api.github.com/users/davanstrien/received_events",
                "type": "User",
                "site_admin": False,
            },
            "content_type": "application/octet-stream",
            "state": "uploaded",
            "size": 5076633,
            "download_count": 0,
            "created_at": "2021-03-31T12:45:59Z",
            "updated_at": "2021-03-31T12:46:03Z",
            "browser_download_url": "https://github.com/davanstrien/learn-onnx/releases/download/2021.03.31/2021-03-31-model.onnx",
        }
    ],
    "tarball_url": "https://api.github.com/repos/davanstrien/learn-onnx/tarball/2021.03.31",
    "zipball_url": "https://api.github.com/repos/davanstrien/learn-onnx/zipball/2021.03.31",
    "body": "\r\n# Description \r\n\r\nblah blah blah\r\n\r\n## Model Metadata\r\n\r\n### Classes\r\n\r\ncat, dog, mouse\r\n\r\n### Scores\r\n\r\n| class | f1 |\r\n|----|---|\r\n|cat | 0.9 |",
}


def test_get_release_metadata_exists(
    test_dict: Dict[Any, Any] = single_github_release_dict
) -> None:
    """It exists"""
    release = models.get_release_metadata(test_dict)
    assert release


def test_get_release_metadata_types(
    test_dict: Dict[Any, Any] = single_github_release_dict
) -> None:
    release = models.get_release_metadata(test_dict)
    assert type(release.html_url) == str


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


@pytest.mark.parametrize(
    "model_dir, expected",
    [
        (Path("20210331"), "2021-03-31 00:00:00"),
        (Path("20210423"), "2021-04-23 00:00:00"),
    ],
)
def test_get_model_date(model_dir: Any, expected: Any) -> None:
    """It returns datetime and str matches"""
    date = models._get_model_date(model_dir)
    assert type(date) == datetime.datetime
    assert str(date) == expected


def test_get_latest_model(tmp_path: Any) -> None:
    flyswot = tmp_path / "flyswot"
    flyswot.mkdir()
    for model in ["20210331", "20210328"]:
        model_path = flyswot / model
        model_path.mkdir()
    latest = models._get_latest_model(flyswot)
    assert latest.name == "20210331"


def test_get_latest_model_none(tmp_path: Any) -> None:
    """It returns None if model directory empty"""
    flyswot = tmp_path / "flyswot"
    flyswot.mkdir()
    latest = models._get_latest_model(flyswot)
    assert latest is None


def test_get_model_parts(tmp_path: Any) -> None:
    model_dir = tmp_path / "20210331/model"
    model_dir.mkdir(parents=True)
    assert model_dir.is_dir()
    vocab = model_dir / "vocab.txt"
    vocab.touch()
    model_card = model_dir / "modelcard.md"
    model_card.touch()
    modelfile = model_dir / "20210331.onnx"
    modelfile.touch()
    parts = models._get_model_parts(tmp_path / "20210331")
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


def test_app(tmp_path: Any) -> None:
    pass
