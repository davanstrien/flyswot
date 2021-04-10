"""Tests model module."""
import datetime

from flyswot import models


def test_app_exists() -> None:
    """It exists"""
    assert models.app


def githubrelease_data_class() -> None:
    """It exists and has right types"""
    date = datetime.datetime.today()
    release = models.GitHubRelease("url", "body", date, "https://google.com", "name")
    assert release
    assert type(release.html_url) == str
