"""Core functionality."""
import mimetypes
import time
from pathlib import Path
from typing import Any
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Set
from typing import Tuple

from toolz import itertoolz  # type: ignore

from flyswot.console import console


image_extensions: Set[str] = {
    k for k, v in mimetypes.types_map.items() if v.startswith("image/")
}


def count_files_with_ext(directory: Path, ext: str) -> int:
    """Counts files matching extension in directory"""
    return itertoolz.count(Path(directory).rglob(f"*{ext}"))


def get_image_files_from_pattern(
    directory: Path, pattern: str, ext: str = None
) -> Iterator[Path]:
    """yield image files from `directory` matching pattern `str` with `ext`"""
    with console.status(
        f"Searching for files matching {pattern} in {directory}...", spinner="dots"
    ):
        time.sleep(1)
        match_files = Path(directory).rglob(f"**/*{pattern}*{ext}")
        for file in match_files:
            if Path(file).suffix in image_extensions:
                yield file
        console.log("Search files complete...")


def filter_to_preferred_ext(files: Iterable[Path], exts: List[str]) -> Iterable[Path]:
    """filter_to_preferred_ext"""
    files = list(files)
    files_without_ext = (
        file.with_suffix("") for file in files if not file.name.startswith(".")
    )
    file_names_without_ext = (file.name for file in files_without_ext)
    unique = set(itertoolz.unique(file_names_without_ext))
    for file in files:
        file_without_suffix = file.with_suffix("")
        for ext in exts:
            if file_without_suffix.name in unique:
                if file.with_suffix(ext).is_file():
                    yield file.with_suffix(ext)
                else:
                    yield file
                unique.discard(file_without_suffix.name)


def signal_last(it: Iterable[Any]) -> Iterable[Tuple[bool, Any]]:
    """returns original iterator and iterator yield false until last item in iterator"""
    if not it:
        raise ValueError
    iterable = iter(it)
    ret_var = next(iterable)
    for val in iterable:
        yield False, ret_var
        ret_var = val
    yield True, ret_var
