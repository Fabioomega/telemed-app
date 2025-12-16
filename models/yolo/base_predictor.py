from ultralytics import YOLO
import numpy as np
from typing import List, Tuple, Dict, Any, TypedDict


class DetectorOutputFormat(TypedDict):
    _class: str
    confidence: float
    # centro x, centro y, largura, altura
    bbox: Tuple[int, int, int, int]


class Detector:

    def __init__(self, model_path: str):
        self.model = YOLO(model_path)

    def _predict(
        self, images: List[np.ndarray], conf: float = 0.5
    ) -> List[DetectorOutputFormat]:

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

    def plot(self, images: List[np.ndarray], conf: float = 0.5) -> List[np.ndarray]:
        results = self.model.predict(images, conf=conf)

        return [result.plot() for result in results]
