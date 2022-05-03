"""Inference functionality"""
import csv
import mimetypes
import re
import string
import time
from collections import defaultdict
from collections import OrderedDict
from dataclasses import asdict
from datetime import datetime
from datetime import timedelta
from functools import singledispatch
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import PIL
import typer
from rich import print
from rich.columns import Columns
from rich.layout import Layout
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from toolz import itertoolz
from toolz.dicttoolz import merge
from transformers import AutoFeatureExtractor
from transformers import AutoModelForImageClassification
from transformers import pipeline

from flyswot import core
from flyswot import models
from flyswot.console import console
from flyswot.inference import InferenceSession
from flyswot.inference import MultiLabelImagePredictionItem
from flyswot.inference import MultiPredictionBatch
from flyswot.inference import PredictionBatch
from flyswot.logo import flyswot_logo

app = typer.Typer()


image_extensions = {k for k, v in mimetypes.types_map.items() if v.startswith("image/")}


@app.command()
def predict_image(
    image: Path = typer.Argument(..., readable=True, resolve_path=True)
) -> None:
    """Predict a single image"""
    pass  # pragma: no cover


def check_files(files: List, pattern: str, directory: Path) -> None:
    """Check if files exist and raises error if not"""
    if not files:
        typer.echo(
            f"Didn't find any files maching {pattern} in {directory}, please check the inputs to flyswot"
        )
        raise typer.Exit(code=1)


def try_predict_batch(batch, inference_session, bs):
    """try and predict a batch of files"""
    bad_batch = False
    try:
        batch_predictions = inference_session.predict_batch(batch, bs)
        return batch_predictions, bad_batch
    except PIL.UnidentifiedImageError:
        bad_batch = True
        return batch, bad_batch


def predict_files(
    files: List[Path], inference_session, bs, csv_fname
) -> Tuple[set, int]:
    """Predict files"""
    with typer.progressbar(length=len(files)) as progress:
        images_checked = 0
        bad_batch_files = []
        for i, batch in enumerate(itertoolz.partition_all(bs, files)):
            batch_predictions, bad_batch = try_predict_batch(
                batch, inference_session, bs
            )
            if bad_batch:
                bad_batch_files.append(batch)
            if i == 0 and not bad_batch:
                create_csv_header(batch_predictions, csv_fname)
            if not bad_batch:
                write_batch_preds_to_csv(batch_predictions, csv_fname)
            progress.update(len(batch))
            images_checked += len(batch)
        corrupt_images = set()
        if bad_batch_files:
            for batch in bad_batch_files:
                for file in batch:
                    try:
                        batch_predictions = inference_session.predict_batch([file], bs)
                        write_batch_preds_to_csv(batch_predictions, csv_fname)
                    except PIL.UnidentifiedImageError:
                        corrupt_images.add(file)
        return corrupt_images, images_checked


@app.command(name="directory")
def predict_directory(
    directory: Path = typer.Argument(
        ...,
        readable=True,
        resolve_path=True,
        help="Directory to start searching for images from",
    ),
    csv_save_dir: Path = typer.Argument(
        ...,
        writable=True,
        resolve_path=True,
        help="Directory used to store the csv report",
    ),
    model_id: str = typer.Option(
        "flyswot/convnext-tiny-224_flyswot",
        help="The model flyswot should use for making predictions",
    ),
    model_path: str = None,
    pattern: str = typer.Option("fs", help="Pattern used to filter image filenames"),
    bs: int = typer.Option(16, help="Batch Size"),
    image_formats: List[str] = typer.Option(
        default=[".tif"],
        help="Image format for flyswot to use for predictions, defaults to `*.tif`",
    ),
):
    """Predicts against all images stored under DIRECTORY which match PATTERN in the filename.

    By default searches for filenames containing 'fs'.

    Creates a CSV report saved to `csv_save_dir`
    """
    start_time = time.perf_counter()
    huggingfaceinference = HuggingFaceInferenceSession(model=model_id)
    files = sorted(
        itertoolz.concat(
            core.get_image_files_from_pattern(directory, pattern, image_format)
            for image_format in image_formats
        )
    )
    check_files(files, pattern, directory)
    typer.echo(f"Found {len(files)} files matching {pattern} in {directory}")
    csv_fname = create_csv_fname(csv_save_dir)
    corrupt_images, images_checked = predict_files(
        files, inference_session=huggingfaceinference, bs=bs, csv_fname=csv_fname
    )
    if corrupt_images:
        print(corrupt_images)
    delta = timedelta(seconds=time.perf_counter() - start_time)
    print_inference_summary(
        str(delta), pattern, directory, csv_fname, image_formats, images_checked
    )
    print(models.hub_model_link(model_id))


def print_inference_summary(
    time_delta: str,
    pattern: str,
    directory: Path,
    csv_fname: Path,
    image_format: Union[List[str], str],
    matched_file_count: int,
    local_model: Optional[models.LocalModel] = None,
):
    """prints summary report"""
    print(flyswot_logo())
    print(
        Panel(
            Text(
                f"CSV report file at: {csv_fname.as_uri()}",
            ),
            title=" :clipboard: CSV report :clipboard:",
        )
    )
    print(
        Panel(
            Text(f"{time_delta}", justify="center", style="bold green"),
            title=":stopwatch: Time taken to run :stopwatch:",
        )
    )
    print(
        create_file_summary_markdown(
            pattern, matched_file_count, directory, image_format
        )
    )
    inference_summary_columns = get_inference_table_columns(csv_fname)
    print(Panel(inference_summary_columns, title="Prediction Summary"))
    if local_model is not None:
        print(models.show_model_card(localmodel=local_model))


def create_file_summary_markdown(
    pattern: str,
    matched_file_count: int,
    directory: Path,
    image_formats: Union[List[str], str],
) -> Panel:
    """creates Markdown summary containing number of files checked by flyswot vs total images files under directory"""
    if isinstance(image_formats, list):
        counts = [core.count_files_with_ext(directory, ext) for ext in image_formats]
        return sum(counts)
    total_image_file_count = core.count_files_with_ext(directory, image_formats)

    return Panel(
        Markdown(
            f"""
    - flyswot searched for image files by matching the patern *{pattern}* with extension(s) {image_formats}
    - flyswot search inside: `{directory}`
    - In total the directory contained **{total_image_file_count}** images
    - There were **{matched_file_count}** files matching the {pattern}* pattern which flyswot checked
    """
        ),
        title=":file_folder: files checked :file_folder:",
    )


def get_inference_table_columns(csv_fname: Path) -> Columns:
    """print_inference_summary from `fname`"""
    labels_to_print = labels_from_csv(csv_fname)
    tables = [
        print_table(labels, f"Prediction summary {i+1}", print=False)
        for i, labels in enumerate(labels_to_print)
    ]
    return Columns(tables)


label_regex = re.compile(r"prediction_label_\D_0")


def labels_from_csv(fname: Path) -> List[List[str]]:
    """Gets top labels from csv `fname`"""
    columns = defaultdict(list)
    with open(fname, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for (k, v) in row.items():
                columns[k].append(v)
    return [columns[k] for k in columns if label_regex.match(k)]


def print_table(
    decoded: list, header: str = "Prediction summary", print: bool = True
) -> Table:
    """Prints table summary of predicted labels"""
    table = Table(show_header=True, title=header)
    table.add_column(
        "Class",
    )
    table.add_column("Count")
    table.add_column("Percentage")
    total = len(decoded)
    frequencies = itertoolz.frequencies(decoded)
    for is_last_element, var in core.signal_last(frequencies.items()):
        key, value = var
        count = value
        percentage = round((count / total) * 100, 2)
        if is_last_element:
            table.add_row(key, str(count), f"{percentage}", end_section=True)
            table.add_row("Total", str(total), "")
        else:
            table.add_row(key, str(count), f"{percentage}")
    if print:
        console.print(table)
    return table


def make_layout():
    """Define the layout."""
    layout = Layout(name="root")
    layout.split(Layout(name="header", size=4), Layout(name="main"))
    layout["main"].split_column(
        Layout(name="info", size=4), Layout(name="body", ratio=2, minimum_size=60)
    )
    layout["info"].split_row(Layout(name="time"), Layout(name="files"))
    return layout


# def print_summary(columns, time, files):
#     layout = make_layout()
#     MARKDOWN = """
#     # Prediction summary
#     """
#     md = Markdown(MARKDOWN)
#     layout["header"].update(md)
#     layout["body"].update(columns)
#     layout["time"].update(time)
#     layout["files"].update(f"Number of files checked {len(files)}")
#     print(layout)


def create_csv_fname(csv_directory: Path) -> Path:
    """Creates a csv filename"""
    date_now = datetime.now()
    date_now = date_now.strftime("%Y_%m_%d_%H_%M")
    fname = Path(f"{date_now}.csv")
    return Path(csv_directory / fname)


@singledispatch
def create_csv_header(batch, csv_path) -> None:
    """Print csv header"""
    raise NotImplementedError(f"Not implemented for type {batch}")


@create_csv_header.register
def _(batch: PredictionBatch, csv_path):
    """Creates a header for csv `csv_path`"""
    with open(csv_path, mode="w", newline="") as csv_file:
        field_names = ["path", "directory", "prediction", "confidence"]
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()


@create_csv_header.register
def _(batch: MultiPredictionBatch, csv_path: Path, top_n: int = 2):
    item = batch.batch[0]
    pred = OrderedDict()
    pred["path"] = asdict(item)["path"]
    pred["directory"] = asdict(item)["path"].parent
    for i, _ in enumerate(item.predictions):
        for j in range(top_n):
            pred[f"prediction_label_{string.ascii_letters[i]}_{j}"] = ""
            pred[f"confidence_label_{string.ascii_letters[i]}_{j}"] = ""
    with open(csv_path, mode="w", newline="") as csv_file:
        field_names = list(pred.keys())
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()


@singledispatch
def write_batch_preds_to_csv(predictions, csv_fpath: Path) -> None:
    """print batch preds to csv"""
    raise NotImplementedError(f"Not implemented for type {predictions}")


@write_batch_preds_to_csv.register
def _(predictions: PredictionBatch, csv_fpath: Path) -> None:
    """Appends `predictions` batch to `csv_path`"""
    with open(csv_fpath, mode="a", newline="") as csv_file:
        field_names = ["path", "directory", "predicted_label", "confidence"]
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        for pred in predictions.batch:
            row = asdict(pred)
            row["directory"] = pred.path.parent
            writer.writerow(row)


@write_batch_preds_to_csv.register
def _(predictions: MultiPredictionBatch, csv_fpath: Path, top_n: int = 2) -> None:
    for pred in predictions.batch:
        row = OrderedDict()
        row["path"] = asdict(pred)["path"]
        row["directory"] = asdict(pred)["path"].parent
        for i, v in enumerate(pred.predictions):
            sorted_predictions = sorted(v.items(), reverse=True)
            for j in range(top_n):
                row[f"prediction_label_{i}_{j}"] = sorted_predictions[j][1]
                row[f"confidence_label_{i}_{j}"] = sorted_predictions[j][0]
        with open(csv_fpath, mode="a", newline="") as csv_file:
            field_names = list(row.keys())
            writer = csv.DictWriter(csv_file, fieldnames=field_names)
            writer.writerow(row)


class HuggingFaceInferenceSession(InferenceSession):
    "Huggingface inference session"

    def __init__(self, model: str):
        """Create Hugging Face Inference Session"""
        self.model = AutoModelForImageClassification.from_pretrained(model)
        self.feature_extractor = AutoFeatureExtractor.from_pretrained(model)
        self.session = pipeline(
            "image-classification",
            model=self.model,
            feature_extractor=self.feature_extractor,
        )

    def predict_image(self, image: Path):
        """Predict single Image."""
        return self.session(image, top_k=10)

    def predict_batch(self, batch: Iterable[Path], bs: int):
        """Predict batch of images"""
        str_batch = [str(file) for file in batch]
        predictions: List[List[Dict[Any]]] = self.session(
            str_batch, batch_size=bs, top_k=20
        )
        prediction_dicts = [self._process_prediction_dict(pred) for pred in predictions]
        all_pred = []
        for file, pred in zip(str_batch, prediction_dicts):
            # flysheet_other_pred = self._create_flysheet_other_predictions(pred)
            item_pred = [pred]
            prediction = MultiLabelImagePredictionItem(Path(file), item_pred)
            all_pred.append(prediction)
        return MultiPredictionBatch(all_pred)

    def _process_prediction_dict(
        self, prediction_item: List[Dict[str, float]]
    ) -> Dict[float, str]:
        return merge(
            [
                {prediction["score"]: prediction["label"]}
                for prediction in prediction_item
            ]
        )


if __name__ == "__main__":
    app()  # pragma: no cover
