from rich.text import Text


def flyswot_logo() -> Text:
    """flyswot logo"""
    return Text(
        r"""
    ______                          __
   / __/ /_  ________      ______  / /_
  / /_/ / / / / ___/ | /| / / __ \/ __/
 / __/ / /_/ (__  )| |/ |/ / /_/ / /_
/_/ /_/\__, /____/ |__/|__/\____/\__/
      /____/


""",
        justify="center",
    )
