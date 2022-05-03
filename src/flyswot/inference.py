"""Core inference functionality."""
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict
from typing import Iterable
from typing import List
from typing import Union


class InferenceSession(ABC):
    """Abstract class for inference sessions"""

    @abstractmethod
    def __init__(self, model: Union[str, Path]):  # pragma: no cover
        """Inference Sessions should init from a model file and vocab"""
        pass

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


@dataclass
class ImagePredictionArgmaxItem:
    """Most confident predicted label for an item.

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

    batch: List[ImagePredictionArgmaxItem]

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
