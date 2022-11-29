"""Core functionality."""
import fnmatch
import mimetypes
import os
import time
from pathlib import Path
from typing import Any
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

from loguru import logger
from toolz import itertoolz  # type: ignore

from flyswot.console import console

IMAGE_EXTENSIONS: Set[str] = {
    k for k, v in mimetypes.types_map.items() if v.startswith("image/")
}


def count_files_with_ext(directory: Path, ext: str) -> int:
    """Counts files matching extension in directory"""
    return itertoolz.count(Path(directory).rglob(f"*{ext}"))


def create_file_search_message(
    directory: Path, pattern: Optional[str], ext: Optional[str]
) -> str:
    """Creates a message to show pattern and ext used for search"""
    if pattern and ext:
        message = f"Searching for files in {directory} matching {pattern} with extension {ext}"
    if pattern and not ext:
        message = f"Searching for image files in {directory} matching {pattern}"
    if not pattern and ext:
        message = f"Searching for all image files in {directory} with extension {ext}"
    if not pattern and not ext:
        message = f"Searching for all image files in {directory}"
    return message


#
# @logger.catch()
# def get_image_files_from_pattern(
#     directory: Path, pattern: Optional[str], ext: Optional[str]
# ) -> Iterator[Path]:
#     """yield image files from `directory` matching pattern `str` with `ext`"""
#     message = create_file_search_message(directory, pattern, ext)
#     with console.status(message, spinner="dots"):
#         time.sleep(1)
#         if pattern:
#             yield from Path(directory).rglob(f"**/*{pattern}*{ext}")
#             console.log("Search files complete...")
#         if pattern and not ext:
#             yield from Path(directory).rglob(f"*{pattern}*")
#         if not pattern and ext:
#             yield from Path(directory).rglob(f"*{ext}")
#         if not pattern and not ext:
#             match_files = Path(directory).rglob("*")
#             for file in match_files:
#                 if file.suffix in image_extensions:
#                     yield file


def yield_all_files(directory: Path) -> Iterator[Path]:  # pragma: no cover
    """Yield all files recursively from directory."""
    with os.scandir(directory) as it:
        for entry in it:
            if entry.is_dir():
                yield from yield_all_files(entry.path)
            if entry.is_file:
                yield Path(entry)


def file_can_be_read(path) -> bool:  # pragma: no cover
    """Checks if a file can be opened."""
    return os.access(path, os.R_OK)


def filter_readable_files(files: Iterator[Path]) -> Iterator[Path]:  # pragma: no cover
    """Yields all readable files from files."""
    for file in files:
        if file_can_be_read(file):
            yield file
        else:
            logger.warning(f"Following file can't be read {file}")
            continue


@logger.catch()
def get_image_files_from_pattern(
    directory: Path,
    filename_pattern: Optional[str] = None,
    image_formats: Union[str, Set[str]] = None,
    check_opens: bool = True,
) -> Iterator[Path]:
    """yield image files from `directory` matching pattern with `ext`"""
    message = create_file_search_message(directory, filename_pattern, image_formats)
    with console.status(message, spinner="dots"):
        time.sleep(1)
        all_files = yield_all_files(directory)
        if check_opens:
            all_files = filter_readable_files(all_files)
        for file in all_files:
            name = file.name
            filename_pattern = f"*{filename_pattern}*" if filename_pattern else "*"
            if not image_formats:
                image_formats = IMAGE_EXTENSIONS
            if isinstance(image_formats, str):
                image_formats = {image_formats}
            if fnmatch.fnmatch(name, filename_pattern) and file.suffix in image_formats:
                yield file


@logger.catch()
def filter_to_preferred_ext(files: Iterable[Path], exts: List[str]) -> Iterable[Path]:
    """Filter files to preferred extension."""
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
