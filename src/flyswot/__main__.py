"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """flyswot."""


if __name__ == "__main__":
    main(prog_name="flyswot")  # pragma: no cover
