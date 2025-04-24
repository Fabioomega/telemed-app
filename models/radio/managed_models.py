import numpy as np
from typing import List, Dict
from service_streamer import ManagedModel, Streamer
from .model import (
    load_modality_model,
    load_multiple_diseases_model,
    load_region_model,
    load_pneumonia_model,
)
from functools import lru_cache


class ModalityModel(ManagedModel):

    def init_model(self):
        self.model = load_modality_model()

    def predict(self, batch: List[np.ndarray]) -> List[Dict[str, bool]]:
        predictions = self.model.predict_by_list(batch)
        return self.model.match_labels(predictions)


class MultipleDiseasesModel(ManagedModel):

    def init_model(self):
        self.main_model = load_multiple_diseases_model()
        self.pneumonia_model = load_pneumonia_model()

    def predict(self, batch: List[np.ndarray]) -> List[Dict[str, bool]]:
        main_predictions = self.main_model.predict_by_list(batch)
        main_predictions = self.main_model.match_labels(main_predictions)

        pneumonia_predictions = self.pneumonia_model.predict_by_list(batch)
        pneumonia_predictions = self.pneumonia_model.match_labels_thresholded(
            pneumonia_predictions
        )

        for i in range(len(main_predictions)):
            if main_predictions[i]["normal"] and not pneumonia_predictions[i]["normal"]:
                main_predictions[i]["normal"] = False
            main_predictions[i]["pneumonia"] = not pneumonia_predictions[i]["normal"]

        return main_predictions


class RegionModel(ManagedModel):

    def init_model(self):
        self.model = load_region_model()

    def predict(self, batch: List[np.ndarray]) -> List[Dict[str, bool]]:
        predictions = self.model.predict_by_list(batch)
        return self.model.match_labels(predictions)


@lru_cache(maxsize=1)
def create_modality(cuda_devices, batch_size, max_latency, worker_num):
    return Streamer(ModalityModel, batch_size, max_latency, worker_num, cuda_devices)


@lru_cache(maxsize=1)
def create_diseases(cuda_devices, batch_size, max_latency, worker_num):
    return Streamer(
        MultipleDiseasesModel, batch_size, max_latency, worker_num, cuda_devices
    )


@lru_cache(maxsize=1)
def create_region(cuda_devices, batch_size, max_latency, worker_num):
    return Streamer(RegionModel, batch_size, max_latency, worker_num, cuda_devices)
