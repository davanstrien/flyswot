"""Inference functionality"""
import csv
import mimetypes
from abc import ABC
from abc import abstractmethod
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import IO
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Union

import numpy as np
import onnxruntime as rt
import PIL
import typer
from PIL import Image
from rich.progress import Progress
from rich.table import Table
from toolz import itertoolz  # type: ignore

from flyswot import core
from flyswot import models
from flyswot.console import console

try:
    from fastai.vision.all import Learner
    from fastai.vision.all import load_learner
except ImportError:
    pass
from importlib import resources

app = typer.Typer()


# flake8: noqa
@dataclass()
class ImagePredictionItem:
    """Prediction for an image.

    Attributes:
        path: The Path to the image
        predicted_label: The predicted label i.e. the argmax value for the prediction tensor
        condidence: The confidence for `predicted_label` i.e. the max value for prediction tensor
    """

    path: Path
    predicted_label: str
    confidence: float

    def __post_init__(self) -> Union[Path, None]:
        try:
            self.path: Path = self.path.absolute()
        except AttributeError:
            pass


@dataclass
class PredictionBatch:
    """Container for ImagePredictionItems"""

    batch: List[ImagePredictionItem]

    def __post_init__(self):
        self.batch_labels: Iterator[str] = (item.predicted_label for item in self.batch)


image_extensions = {k for k, v in mimetypes.types_map.items() if v.startswith("image/")}


@app.command()
def predict_image(
    image: Path = typer.Argument(..., readable=True, resolve_path=True)
) -> None:
    pass  # pragma: no cover


@app.command(name="directory")
def predict_directory(
    directory: Path = typer.Argument(..., readable=True, resolve_path=True),
    csv_save_dir: Path = typer.Argument(
        ...,
        writable=True,
        resolve_path=True,
    ),
    pattern: str = typer.Option("fse"),
    bs: int = typer.Option(32),
    preferred_format: str = typer.Option(
        ".tif",
        help="Preferred image format for predictions. If not available, flyswot will use images matching `pattern`",
    ),
):
    """
    Predicts against all images containing PATTERN in the filename found under DIRECTORY.
    By default searches for filenames containing FSE
    Creates a CSV report saved to CSV_SAVE_DIR containing the predictions
    """
    typer.echo(csv_save_dir)
    model_dir = models.ensure_model_dir()
    typer.echo(model_dir)
    # TODO add load learner function that can be passed a model name
    model_parts = models.ensure_model(model_dir)
    model = model_parts.model
    vocab = models.load_vocab(model_parts.vocab)
    OnnxInference = onnx_inference_session(model, vocab)
    files = core.get_image_files_from_pattern(directory, pattern)
    filtered_files = core.filter_to_preferred_ext(files, preferred_format)
    files = list(filtered_files)
    typer.echo(f"Found {len(files)} files matching {pattern} in {directory}")
    csv_fname = create_csv_fname(csv_save_dir)
    create_csv_header(csv_fname)
    with Progress() as progress:
        prediction_progress = progress.add_task("Predicting images", total=len(files))
        all_preds = []
        predictions = []
        for batch in itertoolz.partition_all(bs, files):
            batch_predictions = OnnxInference.predict_batch(batch, bs)
            all_preds.append(batch_predictions.batch_labels)
            predictions.append(batch_predictions)
            progress.update(prediction_progress, advance=bs)
            write_batch_preds_to_csv(csv_fname, batch_predictions)
        all_preds = list(itertoolz.concat(all_preds))
    print_table(all_preds)


def print_table(decoded) -> None:
    table = Table(show_header=True, title="Prediction summary")
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
    console.print(table)


def create_csv_fname(csv_directory: Path) -> Path:
    date_now = datetime.now()
    date_now = date_now.strftime("%Y_%m_%d_%H_%M")
    fname = Path(date_now + ".csv")
    return Path(csv_directory / fname)


def create_csv_header(csv_path: Path) -> None:
    with open(csv_path, mode="w") as csv_file:
        field_names = ["path", "directory", "predicted_label", "confidence"]
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()


def write_batch_preds_to_csv(csv_fpath: Path, predictions: PredictionBatch) -> None:
    with open(csv_fpath, mode="a") as csv_file:
        field_names = ["path", "directory", "predicted_label", "confidence"]
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        for pred in predictions.batch:
            row = asdict(pred)
            row["directory"] = pred.path.parent
            writer.writerow(row)


class InferenceSession(ABC):
    @abstractmethod
    def __init__(self, model: Path, vocab: List):
        self.model = model
        self.vocab = vocab

    @abstractmethod
    def predict_image(self, image: Path):
        pass

    @abstractmethod
    def predict_batch(self, model: Path, batch: Iterable[Path], bs: int):
        pass


def softmax(x):
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


class onnx_inference_session(InferenceSession):
    """Class for running inference making use of the onnxrunntime"""

    def __init__(self, model, vocab):
        self.model = model
        self.session = rt.InferenceSession(str(model))

        self.vocab = vocab
        self.vocab_mapping = dict(enumerate(self.vocab))

    def _load_vocab(self, vocab: Path) -> List:
        with open(vocab, "r") as f:
            return [item.strip("\n") for item in f.readlines()]

    def predict_image(self, image: Path):
        """Predict a single image"""
        img = self._load_image(image)
        raw_result = self.session.run(["output"], {"image": img})
        pred = self._postprocess(raw_result)
        arg_max = int(np.array(pred).argmax())
        predicted_label = self.vocab_mapping[int(arg_max)]
        confidence = float(np.array(pred).max())
        return ImagePredictionItem(image, predicted_label, confidence)

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

    def predict_batch(self, batch: Iterable[Path], bs: int):
        """predicts a batch of images"""
        prediction_items = [self.predict_image(file) for file in batch]
        return PredictionBatch(prediction_items)


if __name__ == "__main__":
    app()
