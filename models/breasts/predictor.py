from ultralytics import YOLO
import numpy as np
from typing import List, Tuple, Dict, Any, TypedDict


class BreastDetectorOutputFormat(TypedDict):
    _class: str
    confidence: float
    # centro x, centro y, largura, altura
    bbox: Tuple[int, int, int, int]


class BreastDetector:

    def __init__(self, model_path: str):
        self.model = YOLO(model_path)

    def predict(
        self, images: List[np.ndarray], conf: float = 0.5
    ) -> List[BreastDetectorOutputFormat]:

        results = self.model.predict(images, conf=conf)

        batch_detections = []

        for result in results:
            image_detections = []

            for box in result.boxes:
                detection = {
                    "_class": result.names[int(box.cls)],
                    "confidence": float(box.conf),
                    # xywh: centro x, centro y, largura, altura
                    "bbox": box.xywh[0].tolist(),
                }
                image_detections.append(detection)

            batch_detections.append(image_detections)

        return batch_detections


import pathlib

_BASE_PATH = pathlib.Path(__file__).parent
_WEIGHTS_PATH = _BASE_PATH.joinpath("weights")

load_breast_detector_model = lambda: BreastDetector(
    _WEIGHTS_PATH.joinpath("TODO.pt"),
)
