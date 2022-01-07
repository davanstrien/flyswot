"""flyswot command line"""
import typer

from flyswot import inference
from flyswot import models

app = typer.Typer()

app.add_typer(
    inference.app, name="predict", help="flyswot commands for making predictions"
)
app.add_typer(
    models.app, name="model", help="flyswot commands for interacting with models"
)

typer_click_object = typer.main.get_command(app)


def main() -> None:  # pragma: no cover
    """flyswot command line application"""
    app()
