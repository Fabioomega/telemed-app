import torch
import json
from safetensors.torch import load_file, save_file
from transformers import CLIPVisionModel, CLIPImageProcessor
from PIL import Image
from typing import Dict, List, Tuple, Iterable
import numpy as np
import torch.nn.functional as F


class CLIPVisionClassifier(torch.nn.Module):
    def __init__(
        self, num_labels: int, model_name: str = "openai/clip-vit-large-patch14"
    ):
        super().__init__()
        self.clip_vision = CLIPVisionModel.from_pretrained(model_name)
        hidden_size = self.clip_vision.config.hidden_size
        self.classifier = torch.nn.Linear(hidden_size, num_labels)

    def forward(self, pixel_values):
        outputs = self.clip_vision(pixel_values=pixel_values)
        pooled_output = outputs.pooler_output
        logits = self.classifier(pooled_output)
        return logits


def load_image(image_path: str, feature_extractor) -> torch.Tensor:
    image = Image.open(image_path).convert("RGB")
    encoding = feature_extractor(image, return_tensors="pt")
    pixel_values = encoding["pixel_values"].squeeze(0)
    return pixel_values


def load_json(json_path: str) -> Dict:
    with open(json_path, "r", encoding="utf-8") as file:
        return json.load(file)


def map_tensor_to_id(
    tensor: Tuple[torch.IntTensor], id_mapping: Dict[int, str]
) -> List[str]:
    return [id_mapping[int(t.item())] for t in tensor]


def map_list_to_unique_id(l: List[int], id_mapping: Dict[int, str]) -> List[str]:
    return [id_mapping[idx] for idx in set(l)]


def map_tensor_to_nonzero_list(tensor: torch.IntTensor) -> Iterable[List[int]]:
    return [torch.where(row > 0.5)[0].tolist() for row in (tensor > 0.5)]


def pack_to_dict(pack: List[str], label: str) -> List[Dict[str, str]]:
    return [{label: p} for p in pack]

class CLIPVisionModelWrapper:
    def __init__(
        self,
        model_path: str,
        label_json: str,
    ):
        self.label_to_id = load_json(label_json)
        self.id_to_label = {
            v: k for k, v in self.label_to_id.items()
        }
        self.num_labels = len(self.id_to_label)

        self.model = CLIPVisionClassifier(
            num_labels=self.num_labels
        )
        model_state = load_file(model_path)
        self.model.load_state_dict(model_state)
        self.model.eval()

        self.feature_extractor = CLIPImageProcessor.from_pretrained(
            "openai/clip-vit-large-patch14"
        )

        self.feedback_data = []

    def predict(
        self, images: List[np.ndarray] | List[str] | List[Image.Image]
    ) -> List[Dict[str, str]]:
        if not isinstance(images, List) or len(images) == 0:
            raise ValueError("Inputs is not a list or is empty!")

        if isinstance(images[0], str):
            image = [Image.open(image).convert("RGB") for image in images]
            inputs = self.feature_extractor(image, return_tensors="pt")["pixel_values"]
        elif isinstance(images[0], Image.Image) or isinstance(images[0], np.ndarray):
            inputs = self.feature_extractor(images, return_tensors="pt")["pixel_values"]
        else:
            raise TypeError(
                f"Inputs should be of type List[np.ndarray] | List[str] | List[Image.Image] but got {type(images)}"
            )

        with torch.no_grad():
            logits = self.model(inputs)
            probs = F.softmax(logits, dim=1)
            pred_idx = torch.argmax(probs, dim=1).chunk(len(images))
            labels = map_tensor_to_id(
                pred_idx, self.id_to_label
            )

        result = pack_to_dict(labels, "gravidade")

        return result

    def predict_by_path(self, image_path: str) -> List[Dict[str, str]]:
        return self.predict([image_path])

    def store_feedback_by_path(
        self, image_path: str, true_label: int, model_type: str = "classification"
    ):
        pixel_values = load_image(image_path, self.feature_extractor)
        self.feedback_data.append((pixel_values, true_label, model_type))


import pathlib

_BASE_PATH = pathlib.Path(__file__).parent
_WEIGHTS_PATH = _BASE_PATH.joinpath("weights")

_MODEL_PATH = _WEIGHTS_PATH.joinpath("model.safetensors")
_LABELS_JSON = _BASE_PATH.joinpath("label_to_id.json")

load_clip_model = lambda: CLIPVisionModelWrapper(
    model_path=str(_MODEL_PATH),
    label_json=str(_LABELS_JSON),
)

if __name__ == "__main__":
    model_wrapper = load_clip_model()

    # Example usage:
    sample_image_path = [
        r"samples\Bloqueio divisional_anterossuperior_esquerdo.png",
        r"samples\Fibrilacao atrial_e_Sobrecarga_ventricular_esquerda.png",
    ]
    prediction = model_wrapper.predict(sample_image_path)
    print("Prediction:", prediction)
