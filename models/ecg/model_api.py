import torch
import torch.nn as nn
import json
from safetensors.torch import load_file, save_file
from transformers import CLIPVisionModel, CLIPTextModel, CLIPImageProcessor, CLIPTokenizer
from PIL import Image
from typing import Dict, List, Tuple, Iterable
import numpy as np
import torch.nn.functional as F
from scipy.special import expit


class CLIPClassifier(nn.Module):
    def __init__(self, num_labels, visual_config, text_config, pos_weights=None):
        super().__init__()
        self.clip_vision = CLIPVisionModel(visual_config)
        self.clip_text = CLIPTextModel(text_config)
        
        vision_hidden_size = self.clip_vision.config.hidden_size
        text_hidden_size = self.clip_text.config.hidden_size
        fused_hidden_size = vision_hidden_size + text_hidden_size
        
        self.classifier = nn.Sequential(
            nn.Linear(fused_hidden_size, fused_hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(fused_hidden_size // 2, num_labels)
        )

        if pos_weights is not None:
            pos_weights = torch.clamp(pos_weights, min=0.1, max=10.0)
        self.register_buffer('pos_weight', pos_weights)

    def forward(self, pixel_values, input_ids, attention_mask, labels=None):
        vision_outputs = self.clip_vision(pixel_values=pixel_values)
        image_embed = vision_outputs.pooler_output
        
        text_outputs = self.clip_text(input_ids=input_ids, attention_mask=attention_mask)
        text_embed = text_outputs.pooler_output
        
        fused_embed = torch.cat((image_embed, text_embed), dim=1)

        logits = self.classifier(fused_embed)
    
        loss = None
        if labels is not None:
            labels = labels.float()
            pos_weight_device = self.pos_weight.to(logits.device) if self.pos_weight is not None else None
            loss_fct = nn.BCEWithLogitsLoss(pos_weight=pos_weight_device)
            loss = loss_fct(logits, labels)
            
        output = {"logits": logits}
        if loss is not None:
            output["loss"] = loss

        return output


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
        filtered_label_json: str = None,
        model_name: str = "openai/clip-vit-large-patch14"
    ):
        self.label_to_id = load_json(label_json)
        self.id_to_label = {
            v: k for k, v in self.label_to_id.items()
        }
        self.num_labels = len(self.id_to_label)
        
        if filtered_label_json:
            self.filtered_labels = load_json(filtered_label_json)
            self.filtered_ids = set(self.filtered_labels.values())
        else:
            self.filtered_labels = None
            self.filtered_ids = None

        import pathlib
        descriptions_path = pathlib.Path(label_json).parent.joinpath("label_descriptions.json")
        self.label_descriptions = load_json(str(descriptions_path))

        from transformers import CLIPVisionConfig, CLIPTextConfig
        
        visual_config = CLIPVisionConfig(
            hidden_size=1024,
            intermediate_size=3072,
            num_hidden_layers=24,
            num_attention_heads=16,
            image_size=224,
            patch_size=14
        )
        
        text_config = CLIPTextConfig(
            hidden_size=512,
            intermediate_size=2048,
            num_hidden_layers=12,
            num_attention_heads=8,
            max_position_embeddings=77,
            vocab_size=49408
        )

        self.model = CLIPClassifier(
            num_labels=self.num_labels,
            visual_config=visual_config,
            text_config=text_config
        )
        model_state = load_file(model_path)
        self.model.load_state_dict(model_state, strict=False)
        self.model.eval()

        self.feature_extractor = CLIPImageProcessor.from_pretrained(model_name)
        self.tokenizer = CLIPTokenizer.from_pretrained(model_name)

        self.feedback_data = []

    def format_label_with_description(self, label: str) -> str:
        if label in self.label_descriptions:
            return f"{label}: {self.label_descriptions[label]}"
        return label

    def _format_tabular_to_text(self, tabular_data):
        idade = tabular_data.get("idade_paciente", "unknown")
        sexo = tabular_data.get("sexo_paciente", "unknown")
        altura = tabular_data.get("altura", "unknown")
        peso = tabular_data.get("peso", "unknown")

        intensidade_dor_exame = tabular_data.get("intensidade_dor_exame", 0)
        intensidade_dor_indicacao = tabular_data.get("intensidade_dor_indicacao", 0)

        dor_exame_bool = tabular_data.get("dor_momento_exame_exame", False)
        intensidade_dor_exame = tabular_data.get("intensidade_dor_exame", 0)
        dor_indicacao_bool = tabular_data.get("dor_momento_exame_indicacao", False)
        dor_toracica_bool = tabular_data.get("classificar_dor_toracica", False)
        pre_op_bool = tabular_data.get("pre_operatorio", False)
        febre_reum_bool = tabular_data.get("febre_reumatica", False)

        text = f"A {idade} year old patient, sex {sexo}, height {altura} cm, weight {peso} kg. "
        
        if pre_op_bool:
            text += "The patient is in pre-operative status. "
        else:
            text += "The patient is not in pre-operative status. "

        if febre_reum_bool:
            text += "The patient has a history of rheumatic fever. "
        else:
            text += "The patient has no history of rheumatic fever. "

        if dor_exame_bool:
            text += f"Reports pain at the time of the exam with an intensity of {intensidade_dor_exame}. "
        else:
            text += "Reports no pain at the time of the exam. "

        if dor_indicacao_bool:
            text += f"Reports pain on indication with an intensity of {intensidade_dor_indicacao}. "
        else:
            text += "Reports no pain on indication. "

        if dor_toracica_bool:
            text += "The patient is classified as having chest pain."
        else:
            text += "The patient is not classified as having chest pain."

        return text

    def predict(
        self, images: List[np.ndarray] | List[str] | List[Image.Image], 
        tabular_data: List[Dict],
        threshold: float = 0.5
    ) -> List[Dict[str, str | List[str]]]:
        if not isinstance(images, List) or len(images) == 0:
            raise ValueError("Inputs is not a list or is empty!")

        if not tabular_data or not isinstance(tabular_data, List):
            raise ValueError("tabular_data is required and must be a list!")
        
        if len(tabular_data) != len(images):
            raise ValueError("tabular_data length must match images length")

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
        
        # Process images
        pixel_values = self.feature_extractor(processed_images, return_tensors="pt")["pixel_values"]
        
        # Process text for each tabular data
        text_descriptions = [self._format_tabular_to_text(td) for td in tabular_data]
        text_inputs = self.tokenizer(
            text_descriptions,
            padding=True,
            truncation=True,
            max_length=77,
            return_tensors="pt"
        )

        results = []
        self.model.eval()
        
        with torch.no_grad():
            output = self.model(
                pixel_values=pixel_values,
                input_ids=text_inputs["input_ids"],
                attention_mask=text_inputs["attention_mask"]
            )
            logits = output["logits"]
            probs = expit(logits.cpu().numpy())
            preds = (probs >= threshold).astype(int)
            
            for i in range(len(images)):
                tab_data = tabular_data[i]
                
                preds[i, 6] = 0
                probs[i, 6] = 0.0
                
                predicted_indices = np.where(preds[i] >= threshold)[0]
                predicted_indices = predicted_indices[predicted_indices != 6]
                
                if self.filtered_ids is not None:
                    predicted_indices = [idx for idx in predicted_indices if idx in self.filtered_ids]
                
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

    def predict_by_path(self, image_path: str, tabular_data: Dict, threshold: float = 0.5) -> List[Dict[str, str | List[str]]]:
        return self.predict([image_path], tabular_data=[tabular_data], threshold=threshold)

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
_FILTERED_LABELS_JSON = _BASE_PATH.joinpath("label_to_id_filtered.json")

load_clip_model = lambda: CLIPVisionModelWrapper(
    model_path=str(_MODEL_PATH),
    label_json=str(_LABELS_JSON),
    filtered_label_json=str(_FILTERED_LABELS_JSON)
)

