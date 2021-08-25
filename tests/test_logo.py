"""test console"""
from rich.text import Text

from flyswot.logo import flyswot_logo


def test_logo_exists() -> None:
    "It exists"
    assert flyswot_logo()


def test_logo_is_rich_text() -> None:
    "It is rich.Text"
    assert isinstance(flyswot_logo(), Text)
