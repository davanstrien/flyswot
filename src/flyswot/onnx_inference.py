"""Onnxruntime inference session."""
from pathlib import Path
from typing import Iterable
from typing import List
from typing import Union

import numpy as np
from PIL import Image

from flyswot import models
from flyswot.inference import ImagePredictionArgmaxItem
from flyswot.inference import InferenceSession
from flyswot.inference import MultiLabelImagePredictionItem
from flyswot.inference import MultiPredictionBatch
from flyswot.inference import PredictionBatch

try:  # pragma: no cover
    import onnxruntime as rt
except ImportError:  # pragma: no cover
    print("onnxruntime not found")


def softmax(x):
    """return softmax of `x`"""
    x = x.reshape(-1)
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)


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
    ) -> Union[ImagePredictionArgmaxItem, MultiLabelImagePredictionItem]:
        """Predict a single image"""
        img = self._load_image(image)
        output_names = [o.name for o in self.session.get_outputs()]
        raw_result = self.session.run(output_names, {"image": img})
        if len(self.vocab) < 2:
            pred = self._postprocess(raw_result)
            arg_max = int(np.array(pred).argmax())
            predicted_label = self.vocab_mappings[0][arg_max]
            confidence = float(np.array(pred).max())
            return ImagePredictionArgmaxItem(image, predicted_label, confidence)
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
