"""Tests for cli module."""
import pytest
from typer.testing import CliRunner

from flyswot.cli import app


# flake8: noqa
# mypy: allow-untyped-defs

runner = CliRunner()


def test_main_cli() -> None:
    """Basic tests for Cli"""
    result = runner.invoke(app)
    # assert result.exit_code == 0
    result = runner.invoke(app, ["model", "show-model-dir"])
    # assert "models" in result.stdout
