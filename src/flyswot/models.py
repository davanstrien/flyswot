"""Model Commands."""
import datetime
from dataclasses import dataclass

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
