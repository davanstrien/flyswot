"""Inference functionality"""
import csv
import mimetypes
import re
import string
import time
from abc import ABC
from abc import abstractmethod
from collections import defaultdict
from collections import OrderedDict
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from functools import singledispatch
from pathlib import Path
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Union

import numpy as np
import onnxruntime as rt
import PIL
import typer
from PIL import Image  # type: ignore
from rich import print
from rich.columns import Columns
from rich.layout import Layout
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from toolz import itertoolz

from flyswot import core
from flyswot import models
from flyswot.console import console
from flyswot.logo import flyswot_logo

app = typer.Typer()


@dataclass
class ImagePredictionItem:
    """Prediction for an image.

    Attributes:
        path: The Path to the image
        predicted_label: The predicted label i.e. the argmax value for the prediction tensor
        confidence: The confidence for `predicted_label` i.e. the max value for prediction tensor
    """

    path: Path
    predicted_label: str
    confidence: float

    def __post_init__(self) -> Union[Path, None]:
        """attempt to get absolute path"""
        try:
            self.path: Path = self.path.absolute()
        except AttributeError:
            pass


@dataclass
class MultiLabelImagePredictionItem:
    """Multiple predictions for a single image"""

    path: Path
    predictions: List[Dict[float, str]]

    def _get_top_labels(self) -> List[str]:
        """Get top labels"""
        top_labels = []
        for prediction in self.predictions:
            top_label = sorted(prediction.items(), reverse=True)[0][1]
            top_labels.append(top_label)
        return top_labels

    # Post init that gets top prediction label from predictions
    def __post_init__(self):
        """Get top prediction label"""
        self.predicted_labels = self._get_top_labels()


@dataclass
class PredictionBatch:
    """Container for ImagePredictionItems"""

    batch: List[ImagePredictionItem]

    def __post_init__(self):
        """Returns a iterable of all predicted labels in batch"""
        self.batch_labels: Iterable[str] = (item.predicted_label for item in self.batch)


@dataclass
class MultiPredictionBatch:
    """Container for MultiLabelImagePredictionItems"""

    batch: List[MultiLabelImagePredictionItem]

    def _get_predicted_labels(self) -> Iterable:
        """Returns a iterable of all predicted labels in batch"""
        return (item.predicted_labels for item in self.batch)

    def __post_init__(self):
        """Returns a iterable of lists containing all predicted labels in batch"""
        # self.batch_labels: Iterable = (
        #     list(itertoolz.pluck(0, pred))
        #     for pred in zip(*[o.predictions for o in self.batch])
        # )
        self.batch_labels = self._get_predicted_labels()


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
        typer.echo("Corrupt imagess found in batch")
        bad_batch = True
        return batch, bad_batch


def predict_files(files: List[Path], inference_session, bs, csv_fname) -> set:
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
        for batch in bad_batch_files:
            for file in batch:
                try:
                    batch_predictions = inference_session.predict_batch(files, bs)
                    write_batch_preds_to_csv(batch_predictions)
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
    pattern: str = typer.Option("fs", help="Pattern used to filter image filenames"),
    bs: int = typer.Option(16, help="Batch Size"),
    image_format: str = typer.Option(
        ".tif",
        help="Image format for flyswot to use for predictions, defaults to `*.tif`",
    ),
    model_name: str = typer.Option(
        "latest", help="Which model flyswot should use for making predictions"
    ),
    model_path: str = None,
):
    """Predicts against all images stored under DIRECTORY which match PATTERN in the filename.

    By default searches for filenames containing 'fs'.

    Creates a CSV report saved to `csv_save_dir`
    """
    start_time = time.perf_counter()
    model_dir = models.ensure_model_dir()
    model = models.ensure_model(model_dir)
    onnxinference = OnnxInferenceSession(model.model, model.vocab)
    files = sorted(core.get_image_files_from_pattern(directory, pattern, image_format))
    check_files(files, pattern, directory)
    typer.echo(f"Found {len(files)} files matching {pattern} in {directory}")
    csv_fname = create_csv_fname(csv_save_dir)
    corrupt_images, images_checked = predict_files(
        files, inference_session=onnxinference, bs=bs, csv_fname=csv_fname
    )
    if corrupt_images:
        print(corrupt_images)
    delta = timedelta(seconds=time.perf_counter() - start_time)
    print_inference_summary(
        str(delta), pattern, directory, csv_fname, image_format, images_checked
    )


def print_inference_summary(
    time_delta: str,
    pattern: str,
    directory: Path,
    csv_fname: Path,
    image_format: str,
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
    pattern: str, matched_file_count: int, directory: Path, image_format: str
) -> Panel:
    """creates Markdown summary containing number of files checked by flyswot vs total images files under directory"""
    total_image_file_count = core.count_files_with_ext(directory, image_format)
    return Panel(
        Markdown(
            f"""
    - flyswot searched for image files by matching the patern *{pattern}*
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
    fname = Path(date_now + ".csv")
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


class InferenceSession(ABC):
    """Abstract class for inference sessions"""

    @abstractmethod
    def __init__(self, model: Path, vocab: List):  # pragma: no cover
        """Inference Sessions should init from a model file and vocab"""
        self.model = model
        self.vocab = vocab

    @abstractmethod
    def predict_image(self, image: Path):  # pragma: no cover
        """Predict a single image"""
        pass

    @abstractmethod
    def predict_batch(
        self, model: Path, batch: Iterable[Path], bs: int
    ):  # pragma: no cover
        """Predict a batch"""
        pass


def softmax(x):
    """return softmax of `x`"""
    x = x.reshape(-1)
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)


# class FastaiInferenceModel(InferenceSession):
#     def __init__(self, model):
#         self.model = model
#         self.learn = load_learner(model)

#     def predict_image(self, image: Path) -> Any:
#         return self.learn.predict(image)

#     def predict_batch(self, batch: Iterable[Path], bs: int) -> PredictionBatch:
#         test_dl = self.learn.dls.test_dl(batch, bs=bs)
#         vocab = dict(enumerate(self.learn.dls.vocab))
#         with self.learn.no_bar():
#             fastai_preds: Any = self.learn.get_preds(dl=test_dl, with_decoded=True)
#             prediction_tensors: Iterable[Any] = fastai_preds[0]
#             prediction_items = []
#             for file, pred in zip(batch, prediction_tensors):
#                 arg_max = int(np.array(pred).argmax())
#                 predicted_label = vocab[int(arg_max)]
#                 confidence = float(np.array(pred).max())
#                 prediction_items.append(
#                     ImagePredictionItem(file, predicted_label, confidence)
#                 )
#         return PredictionBatch(prediction_items)


class OnnxInferenceSession(InferenceSession):  # pragma: no cover
    """onnx inference session"""

    def __init__(self, model: Path, vocab: Path):
        """Create onnx session"""
        self.model = model
        self.session = rt.InferenceSession(str(model))

        self.vocab = models.load_vocab(vocab)
        self.vocab_mappings = [dict(enumerate(v)) for v in self.vocab]

    def predict_image(
        self, image: Path
    ) -> Union[ImagePredictionItem, MultiLabelImagePredictionItem]:
        """Predict a single image"""
        img = self._load_image(image)
        output_names = [o.name for o in self.session.get_outputs()]
        raw_result = self.session.run(output_names, {"image": img})
        if len(self.vocab) < 2:
            pred = self._postprocess(raw_result)
            arg_max = int(np.array(pred).argmax())
            predicted_label = self.vocab_mappings[0][int(arg_max)]
            confidence = float(np.array(pred).max())
            return ImagePredictionItem(image, predicted_label, confidence)
        else:
            prediction_dicts = []
            for vocab_map, pred in zip(self.vocab_mappings, raw_result):
                predictions = self._postprocess(pred)
                prediction_dict = {
                    float(prediction): vocab_map[i]
                    for i, prediction in enumerate(predictions)
                }
                prediction_dicts.append(prediction_dict)
        return MultiLabelImagePredictionItem(image, prediction_dicts)

    def _preprocess(self, input_data: np.ndarray) -> np.ndarray:
        # converts the input data into the float32 input for onnx
        img_data = input_data.astype("float32")

        # normalize
        mean_vec = np.array([0.485, 0.456, 0.406])
        stddev_vec = np.array([0.229, 0.224, 0.225])
        norm_img_data = np.zeros(img_data.shape).astype("float32")
        for i in range(img_data.shape[0]):
            norm_img_data[i, :, :] = (
                img_data[i, :, :] / 255 - mean_vec[i]
            ) / stddev_vec[i]

        # add batch channel
        norm_img_data = norm_img_data.reshape(1, 3, 512, 512).astype("float32")
        return norm_img_data

    def _load_image(self, file: Path) -> np.ndarray:
        """loads image and carries out preprocessing for inference"""
        image = Image.open(file, mode="r")
        image = image.resize((512, 512), Image.BILINEAR)
        image_data = np.array(image).transpose(2, 0, 1)
        return self._preprocess(image_data)

    def _postprocess(self, result: List):
        """process results from onnx session"""
        return softmax(np.array(result)).tolist()

    def predict_batch(
        self, batch: Iterable[Path], bs: int
    ) -> Union[PredictionBatch, MultiPredictionBatch]:
        """predicts a batch of images"""
        prediction_items = [self.predict_image(file) for file in batch]
        if len(self.vocab) < 2:
            return PredictionBatch(prediction_items)
        else:
            return MultiPredictionBatch(prediction_items)


if __name__ == "__main__":
    app()  # pragma: no cover
