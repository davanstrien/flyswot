"""main flyswot cli entrypoint"""
import typer

from flyswot import inference
from flyswot import models

app = typer.Typer()
app.add_typer(models.app, name="model")
app.add_typer(inference.app, name="predict")


def main() -> None:
    """flyswot"""
    app()  # pragma: no cover
