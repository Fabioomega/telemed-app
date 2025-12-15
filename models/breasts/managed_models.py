import numpy as np
from typing import List, Dict
from service_streamer import ManagedModel, Streamer
from .predictor import load_breast_detector_model, BreastDetectorOutputFormat
from ..internals import announce_start
from functools import lru_cache


class BreastDetectorModel(ManagedModel):

    def init_model(self):
        self.model = load_breast_detector_model()

    def predict(self, batch: List[np.ndarray]) -> List[BreastDetectorOutputFormat]:
        predictions = self.model.predict(batch)
        return predictions


@lru_cache(maxsize=1)
@announce_start("Breast Cancer Classifier")
def create_breast(cuda_devices, batch_size, max_latency, worker_num):
    return Streamer(
        BreastDetectorModel, batch_size, max_latency, worker_num, cuda_devices
    )
