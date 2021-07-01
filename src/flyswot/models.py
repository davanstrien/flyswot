"""Model Commands."""
import datetime
import fnmatch
import json
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import typer
import validators  # type: ignore
from rich.markdown import Markdown
from toolz import itertoolz
from toolz import recipes

from flyswot.config import APP_NAME
from flyswot.config import MODEL_REPO_URL
from flyswot.console import console

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


@dataclass
class LocalModel:
    """A local model container"""

    vocab: Path
    modelcard: Path
    model: Path


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
    """Checks url is valid"""
    if url == "latest":
        return url
    if validators.url(url):
        return url
    else:
        raise typer.BadParameter(f"Please check {url} is a valid url")


def get_remote_release_json(
    url: str, single: bool = False
) -> Dict[str, Any]:  # pragma : no cover
    """Returns all releases found at `url`"""
    with urllib.request.urlopen(url) as response:  # pragma: no cover
        try:
            html = response.read()
            response_json: Dict[str, Any] = json.loads(html)
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
    """Print out the directory where models are stored"""
    ensure_model_dir()


@app.command(name="download")
def download_model(
    url: str = typer.Argument("latest", callback=_url_callback),
    model_dir: Path = typer.Argument(
        None,
        envvar="MODEL_DIR",
        help="Optionally specify a directory to store model files in",
    ),
) -> None:  # pragma: no cover
    """Downloads models, defaults to the latest available model"""
    if url != "latest":

        raise NotImplementedError
    url = MODEL_REPO_URL + "/latest"
    remote_release_json = get_remote_release_json(url, single=True)
    if not remote_release_json:
        raise typer.Exit()
    release_metadata = get_release_metadata(remote_release_json)
    download_url = release_metadata.browser_download_url
    updated_date = release_metadata.updated_at
    typer.echo(f"Remote model updated on {updated_date}")
    model_dir = ensure_model_dir()
    model_save_path = model_dir / release_metadata.model_name
    with console.status(
        "Downloading model...",
        spinner="aesthetic",
    ):
        urllib.request.urlretrieve(download_url, model_save_path)
    typer.echo(f"Model saving to {model_save_path}...")
    typer.echo("Extracting model...")
    with zipfile.ZipFile(model_save_path, "r") as zip_ref:
        zip_ref.extractall(model_dir / release_metadata.model_name.replace(".zip", ""))


def _get_model_date(model: Path) -> datetime.datetime:
    """Gets the date from a `model_name` fname"""
    return datetime.datetime.strptime(model.name, "%Y%m%d")


def _sort_local_models_by_date(model_dir: Path) -> List[Path]:
    return sorted(
        [
            d
            for d in Path(model_dir).iterdir()
            if (d.is_dir() and not d.name.startswith("."))
        ],
        reverse=True,
    )


def _get_latest_model(model_dir: Path) -> Optional[Path]:
    models = _sort_local_models_by_date(model_dir)
    if not models:
        return None
    else:
        return models[0]


def _get_model_parts(model_dir: Path) -> LocalModel:
    """Returns model path, vocab and metadata for a model"""
    model_files = Path(model_dir / "model").iterdir()
    for file in model_files:
        if fnmatch.fnmatch(file.name, "vocab.txt"):
            vocab = file
        if fnmatch.fnmatch(file.name, "modelcard.md"):
            modelcard = file
        if fnmatch.fnmatch(file.name, "*.onnx") or fnmatch.fnmatch(file.name, "*.pkl"):
            model = file
    return LocalModel(vocab, modelcard, model)


def _compare_remote_local(local_model: Path) -> bool:  # pragma: no cover
    url = MODEL_REPO_URL + "/latest"
    remote_release_json = get_remote_release_json(url, single=True)
    if not remote_release_json:
        raise typer.Exit()
    release_metadata = get_release_metadata(remote_release_json)
    return (
        release_metadata.updated_at.isoformat()
        > _get_model_date(local_model).isoformat()
    )


def load_model(model_dir: Path):  # pragma: no cover
    """returns a local model"""
    return _get_model_parts(model_dir)


def ensure_model(
    model_dir: Path, check_latest: bool = False
) -> Optional[LocalModel]:  # pragma: no cover
    """Checks for a local model and if not found downloads the latest available remote model"""
    local_model = _get_latest_model(model_dir)
    if local_model and not check_latest:
        model_parts = _get_model_parts(local_model)
        return model_parts
    if local_model and check_latest:
        if _compare_remote_local(local_model):
            download_model(url="latest", model_dir=model_dir)
        local_model = _get_latest_model(model_dir)
        if local_model:
            model_parts = _get_model_parts(local_model)
            return model_parts
        else:
            typer.echo("No model found locally...")

    if not local_model:
        download_model(url="latest", model_dir=model_dir)
        local_model = _get_latest_model(model_dir)
        if local_model:
            model_parts = _get_model_parts(local_model)
            return model_parts
        typer.echo("Not able to find a model")
        raise typer.Exit()


def is_pipe(c: Tuple) -> bool:
    """Checks if | in c"""
    return "|" in c


def load_vocab(vocab: Path) -> List[List[str]]:
    """loads vocab from `vocab` and returns as list contaning lists of vocab"""
    with open(vocab, "r") as f:
        raw_vocab = [line.strip("\n") for line in f.readlines()]
        return list(
            map(
                list,
                (itertoolz.remove(is_pipe, (recipes.partitionby(is_pipe, raw_vocab)))),
            )
        )


@app.command()
def vocab(
    model: str = typer.Argument("latest"), show: bool = typer.Option(True)
) -> Optional[List[str]]:
    """Prints out vocab for latest model"""
    if model != "latest":
        raise NotImplementedError
    model_dir = ensure_model_dir()
    model_path = _get_latest_model(model_dir)
    if model_path:
        model_parts = _get_model_parts(model_path)
        if model_parts.vocab:
            vocab = load_vocab(model_parts.vocab)
            if show:
                console.print(Markdown("# Model Vocab"))
                console.print(vocab)
            return vocab


if __name__ == "__main__":  # pragma: no cover
    app()
