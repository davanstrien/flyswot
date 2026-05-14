"""Nox sessions."""

import os
import shutil
from pathlib import Path

import nox

package = "flyswot"
python_versions = ["3.12", "3.11", "3.10"]
nox.options.sessions = (
    "ruff-check",
    "ty",
    "tests",
    "xdoctest",
    "docs-build",
)
nox.options.default_venv_backend = "uv"


@nox.session(name="ruff-check", python="3.12")
def ruff_check(session: nox.Session) -> None:
    """Lint and format-check using ruff."""
    session.install("ruff")
    session.run("ruff", "check", "src", "tests")
    session.run("ruff", "format", "--check", "src", "tests")


@nox.session(python="3.12")
def ty(session: nox.Session) -> None:
    """Type-check using ty."""
    args = session.posargs or ["src"]
    session.install(".[dev]")
    session.run("ty", "check", *args)


@nox.session(python=python_versions)
def tests(session: nox.Session) -> None:
    """Run the test suite under coverage."""
    session.install(".[dev]")
    session.run("coverage", "run", "-m", "pytest", *session.posargs)
    if not session.posargs:
        session.run("coverage", "report")


@nox.session(python=python_versions)
def xdoctest(session: nox.Session) -> None:
    """Run examples with xdoctest."""
    args = session.posargs or ["all"]
    session.install(".[dev]")
    session.run("python", "-m", "xdoctest", package, *args)


@nox.session(name="docs-build", python=python_versions[0])
def docs_build(session: nox.Session) -> None:
    """Build the documentation."""
    session.install(".[docs]")
    args = session.posargs or ["docs", "docs/_build"]
    if not session.posargs and "FORCE_COLOR" in os.environ:
        args.insert(0, "--color")

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-build", *args)


@nox.session(python=python_versions[0])
def docs(session: nox.Session) -> None:
    """Build and serve the documentation with live reloading on file changes."""
    args = session.posargs or ["--open-browser", "docs", "docs/_build"]
    session.install(".[docs]", "sphinx-autobuild")

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-autobuild", *args)
