"""Model Commands."""
import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import requests
import typer
from huggingface_hub import hf_hub_url
from huggingface_hub import snapshot_download
from huggingface_hub.hf_api import ModelInfo
from rich import print
from rich.markdown import Markdown
from rich.table import Table
from toolz import itertoolz
from toolz import recipes

from flyswot.config import APP_NAME
from flyswot.config import MODEL_REPO_ID
from flyswot.console import console

app = typer.Typer()


@dataclass
class LocalModel:
    """A local model container"""

    hf_cache: Path

    def __post_init__(self):
        """Returns model parts contained under hf_cache"""
        self._get_model_parts(self.hf_cache)

    def _get_model_parts(self, hf_cache: Path):
        """Returns model path, vocab and metadata for a model"""
        model_files = Path(hf_cache).iterdir()
        for file in model_files:
            if fnmatch.fnmatch(file.name, "vocab.txt"):
                self.vocab = file
            if fnmatch.fnmatch(file.name, "README.md"):
                self.modelcard = file
            if fnmatch.fnmatch(file.name, "*.onnx") or fnmatch.fnmatch(
                file.name, "*.pkl"
            ):
                self.model = file


def ensure_model_dir(model_dir_path: Union[Path, None] = None) -> Path:
    """Checks for a local model dir and creates one if not found"""
    if not model_dir_path:
        app_dir = typer.get_app_dir(APP_NAME)
        model_dir: Path = Path(app_dir) / "models"
    else:
        model_dir = Path(model_dir_path) / "models"
    if not (model_dir.exists() and model_dir.is_dir()):
        print(f"Creating directory for storing models in {model_dir}...")
        try:
            model_dir.mkdir(parents=True)
        except PermissionError as e:  # pragma: no cover
            print(f"{model_dir} is not writeable: {e}")
            raise typer.Exit(code=1) from None
    print(f"Models stored in {model_dir}")
    return model_dir


@app.command()
def show_model_dir() -> None:
    """Print out the directory where models are stored"""
    ensure_model_dir()


@app.command(name="download")
def get_model(
    revision: Optional[str] = typer.Argument(None),
    model_dir: Path = typer.Argument(
        None,
        envvar="MODEL_DIR",
        help="Optionally specify a directory to store model files in",
    ),
    local_only=False,
) -> Path:  # pragma: no cover
    """Downloads models, defaults to the latest available model"""
    repo_id = MODEL_REPO_ID
    with console.status("Getting model", spinner="dots"):
        model = snapshot_download(
            repo_id, cache_dir=model_dir, revision=None, local_files_only=local_only
        )
    return Path(model)


def ensure_model(model_dir: Path) -> LocalModel:  # pragma: no cover
    """Checks for a local model and if not found downloads the latest available remote model"""
    if model := get_model(model_dir=model_dir):
        return LocalModel(model)
    print("Not able to find a model")
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
def vocab(model: str = typer.Argument("latest"), show: bool = typer.Option(True)):
    """Prints out vocab for latest model"""
    if model != "latest":
        raise NotImplementedError
    model_dir = ensure_model_dir()
    if model_path := get_model(model_dir=model_dir):
        local_model = LocalModel(model_path)
        if local_model.vocab:
            vocab = load_vocab(local_model.vocab)
            if show:
                console.print(Markdown("# Model Vocab"))
                console.print(vocab)
            return vocab


def show_model_card(localmodel: LocalModel):
    """Shows model card for model"""
    with open(localmodel.modelcard, "r") as f:
        md = Markdown(f.read())
    console.print(md)


def hub_model_link(model_id: str) -> str:
    """Creates rich link for model card"""
    url = f"https://huggingface.co/{model_id}"
    return f"View [link={url}]model card[/link] for {model_id}!"


def create_markdown_model_card(model_id: str):
    """Creates rich Markdown wrapper for hub readme"""
    readme_url = hf_hub_url(model_id, filename="README.md")
    r = requests.get(readme_url)
    r.raise_for_status()
    return Markdown(r.text)


def create_metrics_tables(model_info: ModelInfo) -> List[Table]:
    """Creates a list of rich tables for metrics contained in `model_info`"""
    model_indexes = list(model_info.cardData["model-index"])
    metrics = []
    for model in model_indexes:
        for result in model["results"]:
            for metric in result["metrics"]:
                metrics.append(metric)
    for metric in metrics:
        table = Table()
        for name in metric.keys():
            table.add_column(name.title())
    metric_values = list(metric.values())
    rounded_metric_values = [
        round(item, ndigits=3) if isinstance(item, float) else item
        for item in metric_values
    ]
    table.add_row(*list(map(str, rounded_metric_values)))
    return [table]


if __name__ == "__main__":  # pragma: no cover
    app()
