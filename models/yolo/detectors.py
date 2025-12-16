import pathlib
from .base_predictor import Detector

_BASE_PATH = pathlib.Path(__file__).parent
_WEIGHTS_PATH = _BASE_PATH.joinpath("weights")

if False:
    load_breast_detector_model = lambda: Detector(
        _WEIGHTS_PATH.joinpath("TODO.pt"),
    )

load_fracture_detector_model = lambda: Detector(
    _WEIGHTS_PATH.joinpath("fracture-best.pt"),
)
