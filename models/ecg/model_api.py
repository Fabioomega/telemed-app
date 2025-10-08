import torch
import json
from safetensors.torch import load_file, save_file
from transformers import CLIPVisionModel, CLIPImageProcessor
from PIL import Image
from typing import Dict, List, Tuple, Iterable
import numpy as np
import torch.nn.functional as F
from scipy.special import expit


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

        self.label_descriptions = {
            "ADRV": "Alteração Difusa da Repolarização Ventricular",
            "AEI (ZEI)": "Área Eletricamente Inativa (Zona Eletricamente Inativa)",
            "AFCRD": "Atraso Final da Condução pelo Ramo Direito",
            "ARV": "Alteração da Repolarização Ventricular",
            "Desvio Eixo - E": "Desvio do Eixo para a Esquerda",
            "NORMAL/DLN": "Normal/Dentro dos Limites da Normalidade",
            "None": "Baixa confiança ou nenhum descritor suportado",
            "SVE": "Sobrecarga Ventricular Esquerda",
            "TS": "Taquicardia Sinusal"
        }

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

    def format_label_with_description(self, label: str) -> str:
        if label in self.label_descriptions:
            return f"{label}: {self.label_descriptions[label]}"
        return label

    def predict(
        self, images: List[np.ndarray] | List[str] | List[Image.Image], 
        threshold: float = 0.5
    ) -> List[Dict[str, str | List[str]]]:
        if not isinstance(images, List) or len(images) == 0:
            raise ValueError("Inputs is not a list or is empty!")

        processed_images = []
        for img in images:
            if isinstance(img, str):
                processed_images.append(Image.open(img).convert("RGB"))
            elif isinstance(img, np.ndarray):
                processed_images.append(Image.fromarray(img).convert("RGB"))
            elif isinstance(img, Image.Image):
                processed_images.append(img.convert("RGB"))
            else:
                raise TypeError(f"Unsupported image type: {type(img)}")
        
        inputs = self.feature_extractor(processed_images, return_tensors="pt")["pixel_values"]

        results = []
        self.model.eval()
        
        with torch.no_grad():
            logits = self.model(inputs)
            probs = expit(logits.cpu().numpy())
            preds = (probs >= threshold).astype(int)
            
            for i in range(len(images)):

                preds[i, 6] = 0
                probs[i, 6] = 0.0
                
                predicted_indices = np.where(preds[i] >= threshold)[0]
                predicted_indices = predicted_indices[predicted_indices != 6]
                
                if len(predicted_indices) > 0:
                    label_acronyms = [self.id_to_label[idx] for idx in predicted_indices]
                    formatted_labels = [self.format_label_with_description(label) for label in label_acronyms]
                    if len(formatted_labels) == 1:
                        results.append({"gravidade": formatted_labels[0]})
                    else:
                        results.append({"gravidade": formatted_labels})
                else:
                    results.append({"gravidade": "Não Identificado"})
        
        return results

    def predict_by_path(self, image_path: str, threshold: float = 0.5) -> List[Dict[str, str | List[str]]]:
        return self.predict([image_path], threshold=threshold)

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
