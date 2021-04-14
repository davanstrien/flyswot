"""Model Commands."""
import datetime
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Type
from typing import Union

import typer
import validators  # type: ignore

from flyswot.config import APP_NAME
from flyswot.config import MODEL_REPO_URL

# flake8: noqa
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


def get_release_metadata(release: Dict[str, Any]) -> GitHubRelease:
    """Extracts required fields from `release` for `GitHubRelease`"""
    html_url = release["html_url"]
    body = release["body"]
    assets_json = release["assets"][0]
    updated_at = datetime.datetime.strptime(
        assets_json["updated_at"], "%Y-%m-%dT%H:%M:%S%z"
    )
    browser_download_url = assets_json["browser_download_url"]
    name = assets_json["name"]
    return GitHubRelease(html_url, body, updated_at, browser_download_url, name)


def _url_callback(url: str) -> Union[str, None]:
    """Check url appears valid"""
    if url == "latest":
        return url
    if validators.url(url):
        return url
    else:
        raise typer.BadParameter(f"Please check {url} is a valid url")


def get_remote_release_json(
    url: str, single: bool = False
) -> Union[List[Dict[str, Any]], Dict[str, Any], Type[ConnectionError]]:
    """Returns all releases found at `url`"""
    with urllib.request.urlopen(url) as response:
        try:
            html = response.read()
            response_json: Dict[str, Any] = json.loads(html)
            if single:
                return response_json
            else:
                return response_json
        except ConnectionError as error:  # pragma: no cover
            typer.echo(error)
            raise typer.Exit(code=1)


def ensure_model_dir(model_dir_path: Union[Path, None] = None) -> Path:
    """Checks for a local model dir and creates one if not found"""
    if not model_dir_path:
        app_dir = typer.get_app_dir(APP_NAME)
        model_dir: Path = Path(app_dir) / "models"
    else:
        model_dir = Path(model_dir_path) / "models"
    if not (model_dir.exists() and model_dir.is_dir()):
        typer.echo(f"Creating directory for storing models in {model_dir}...")
        try:
            model_dir.mkdir(parents=True)
        except PermissionError as e:  # pragma: no cover
            typer.echo(f"{model_dir} is not writeable: {e}")
            raise typer.Exit(code=1)
    typer.echo(f"Models stored in {model_dir}")
    return model_dir


@app.command()
def show_model_dir() -> None:
    """Print out the directory where modles are stored"""
    ensure_model_dir()


def _create_model_metadata_path(model_name: str) -> str:
    """Creates a filename for model metadata"""
    without_suffix = "".join(model_name.split(".")[:-1])
    return f"{without_suffix}.md"


@app.command(name="download")
def download_model(
    url: str = typer.Argument("latest", callback=_url_callback),
    model_dir: Path = typer.Argument(
        None,
        envvar="MODEL_DIR",
        help="Optionally specify a directory to store model files in",
    ),
) -> None:
    """Downloads models, defaults to the latest available model"""
    if url == "latest":  # pragma: no cover

        url = MODEL_REPO_URL + "/latest"
        remote_release_json = get_remote_release_json(url, single=True)
        if isinstance(remote_release_json, dict):
            release_metadata = get_release_metadata(remote_release_json)
        download_url = release_metadata.browser_download_url
        updated_date = release_metadata.updated_at
        model_description = release_metadata.body
        typer.echo(f"{updated_date} {download_url}")
        model_dir = ensure_model_dir(model_dir)
        model_save_path = model_dir / release_metadata.model_name
        typer.echo(f"Saving model to {model_save_path}...")
        urllib.request.urlretrieve(download_url, model_save_path)
        model_description_path = model_dir / _create_model_metadata_path(
            release_metadata.model_name
        )
        typer.echo(model_description_path)
        with open(model_description_path, "w") as f:
            f.write(model_description)
    else:
        raise NotImplementedError


def _get_model_date(model_name: Path) -> datetime.datetime:
    """Gets the date from a `model_name` fname"""
    stem = Path(model_name).stem.split("-")
    str_date = "-".join(stem[:3])
    return datetime.datetime.strptime(str_date, "%Y-%m-%d")


def _sort_local_models_by_date(model_dir: Path) -> List[Path]:
    models = list(Path(model_dir).rglob("*.pkl"))
    return sorted(models, key=_get_model_date, reverse=True)


if __name__ == "__main__":  # pragma: no cover
    app()
