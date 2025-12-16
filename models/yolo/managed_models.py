import numpy as np
from typing import List, Dict
from service_streamer import ManagedModel, Streamer
from .base_predictor import DetectorOutputFormat
from .detectors import load_fracture_detector_model
from ..internals import announce_start
from functools import lru_cache


if False:

    class BreastDetectorModel(ManagedModel):

        def init_model(self):
            self.model = load_breast_detector_model()

        def predict(self, batch: List[np.ndarray]) -> List[np.ndarray]:
            predictions = self.model.plot(batch)
            return predictions

    @lru_cache(maxsize=1)
    @announce_start("Breast Cancer Classifier")
    def create_fracture(cuda_devices, batch_size, max_latency, worker_num):
        return Streamer(
            BreastDetectorModel, batch_size, max_latency, worker_num, cuda_devices
        )


class FractureDetectorModel(ManagedModel):

    def init_model(self):
        self.model = load_fracture_detector_model()

    def predict(self, batch: List[np.ndarray]) -> List[np.ndarray]:
        predictions = self.model.plot(batch)
        return predictions


@lru_cache(maxsize=1)
@announce_start("Fracture Region Classifier")
def create_fracture(cuda_devices, batch_size, max_latency, worker_num):
    return Streamer(
        FractureDetectorModel, batch_size, max_latency, worker_num, cuda_devices
    )
