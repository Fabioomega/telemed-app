import numpy as np
from typing import List, Dict
from service_streamer import ManagedModel, Streamer
from .model_api import load_clip_model
from functools import lru_cache
from ..internals import announce_start


class ECGClassifier(ManagedModel):

    def init_model(self):
        self.model = load_clip_model()

    def predict(self, batch: List[np.ndarray]) -> List[Dict[str, str]]:
        return self.model.predict(batch)


@lru_cache(maxsize=1)
@announce_start("ECG Classifier")
def create_ecg_classifier(cuda_devices, batch_size, max_latency, worker_num):
    return Streamer(ECGClassifier, batch_size, max_latency, worker_num, cuda_devices)
