"""Model Commands."""
import datetime
from dataclasses import dataclass
from typing import Any
from typing import Dict

import typer

APP_NAME = "flyswot"

app = typer.Typer()

REPO_URL = "https://api.github.com/repos/davanstrien/learn-onnx/releases"


@dataclass
class GitHubRelease:
    """A GitHub Release of a model"""

    html_url: str
    body: str
    updated_at: datetime.datetime
    browser_download_url: str
    model_name: str


def get_release_metadata(release: Dict[Any, Any]) -> GitHubRelease:
    """Extracts required fields from `release` for `GitHubRelease`"""
    html_url = release["html_url"]
    body = release["body"]
    assets_json = release["assets"][0]
    updated_at = datetime.datetime.strptime(assets_json["updated_at"], "%Y-%m-%dT%H:%M:%S%z")
    browser_download_url = assets_json["browser_download_url"]
    name = assets_json["name"]
    return GitHubRelease(html_url, body, updated_at, browser_download_url, name)
