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
        gravidade_model_path: str,
        gravidade_label_json: str,
        grave_model_path: str,
        grave_label_json: str,
    ):
        self.label_to_id_gravidade = load_json(gravidade_label_json)
        self.id_to_label_gravidade = {
            v: k for k, v in self.label_to_id_gravidade.items()
        }
        self.num_labels_gravidade = len(self.label_to_id_gravidade)

        self.label_to_id_grave = load_json(grave_label_json)
        self.id_to_label_grave = {v: k for k, v in self.label_to_id_grave.items()}
        self.num_labels_grave = len(self.label_to_id_grave)

        self.gravidade_model = CLIPVisionClassifier(
            num_labels=self.num_labels_gravidade
        )
        gravidade_state = load_file(gravidade_model_path)
        self.gravidade_model.load_state_dict(gravidade_state)
        self.gravidade_model.eval()

        self.grave_model = CLIPVisionClassifier(num_labels=self.num_labels_grave)
        grave_state = load_file(grave_model_path)
        self.grave_model.load_state_dict(grave_state)
        self.grave_model.eval()

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
                f"Inputs should be of type List[np.ndarray] | List[str] | List[Image.Image] but got {type(inputs)}"
            )

        with torch.no_grad():
            logits_gravidade = self.gravidade_model(inputs)
            probs_gravidade = F.softmax(logits_gravidade, dim=1)
            pred_idx_gravidade = torch.argmax(probs_gravidade, dim=1).chunk(len(images))
            labels_gravidade = map_tensor_to_id(
                pred_idx_gravidade, self.id_to_label_gravidade
            )

        result = pack_to_dict(labels_gravidade, "gravidade")

        indexes = [
            i for i in range(len(images)) if labels_gravidade[i].lower() == "grave"
        ]

        if len(indexes) != 0:
            indexes_set = set(indexes)
            inputs = torch.stack(
                [inp for i, inp in enumerate(inputs) if i in indexes_set]
            )

            with torch.no_grad():
                logits_grave = self.grave_model(inputs)
                probs_grave = torch.sigmoid(logits_grave)
                pred_indices_grave = map_tensor_to_nonzero_list(probs_grave > 0.5)

                for idx, pred_indices in zip(indexes, pred_indices_grave):
                    if pred_indices:
                        result[idx]["grave_classification"] = map_list_to_unique_id(
                            pred_indices, self.id_to_label_grave
                        )
                    else:
                        result[idx]["grave_classification"] = ["Nao Identificado"]

        return result

    def predict_by_path(self, image_path: str) -> Dict:
        return self.predict([image_path])

    def store_feedback_by_path(
        self, image_path: str, true_label: int, model_type: str = "gravidade"
    ):
        pixel_values = load_image([image_path], self.feature_extractor)
        self.feedback_data.append((pixel_values, true_label, model_type))


import pathlib

_BASE_PATH = pathlib.Path(__file__).parent
_WEIGHTS_PATH = _BASE_PATH.joinpath("weights")

_GRAVIDADE_MODEL_PATH = _WEIGHTS_PATH.joinpath("gravidade_model.safetensors")
_GRAVIDADE_LABELS_JSON = _BASE_PATH.joinpath("gravidade_label_to_id.json")
_GRAVE_MODEL_PATH = _WEIGHTS_PATH.joinpath("grave_model.safetensors")
_GRAVE_LABELS_JSON = _BASE_PATH.joinpath("grave_label_to_id.json")

load_clip_model = lambda: CLIPVisionModelWrapper(
    gravidade_model_path=_GRAVIDADE_MODEL_PATH,
    gravidade_label_json=_GRAVIDADE_LABELS_JSON,
    grave_model_path=_GRAVE_MODEL_PATH,
    grave_label_json=_GRAVE_LABELS_JSON,
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
