import numpy as np
import tensorflow as tf
import json
from keras._tf_keras.keras.models import load_model
from PIL import Image
from typing import Tuple, List, Dict


def load_image(image_path: str) -> np.ndarray:
    return np.array(Image.open(image_path))


def load_json(json_path: str) -> Dict:
    with open(json_path, encoding="utf-8") as file:
        return json.load(file)


def preprocess_batch(imgs: np.ndarray, img_size: Tuple[int, int]):
    imgs = tf.image.resize(imgs, img_size)
    if imgs.shape[-1] == 1:
        imgs = tf.expand_dims(imgs, axis=-1)
        imgs = tf.image.grayscale_to_rgb(imgs)
    imgs = imgs / 255
    return imgs


def set_max_true(batch):
    # Find the indices of the maximum values in each row
    max_indices = np.argmax(batch, axis=1)

    # Create a boolean mask with the same shape as batch
    mask = np.zeros_like(batch, dtype=bool)

    # Set the maximum values to True
    mask[np.arange(batch.shape[0]), max_indices] = True

    return mask


class ConvolutionalModel:
    def __init__(self, model_path: str, labels: Dict[int, str], input_size=(224, 224)):
        self.model = load_model(model_path)
        self.input_size = input_size
        self.feedback_data = list()
        self.labels = labels.values()

    def get_qtd_classes(self):
        return self.model.layers[-1].units

    def raw_match_labels(self, logits: np.ndarray) -> Dict[str, float]:
        per = tf.nn.softmax(logits)
        # Shape: (B, classes)
        return dict(zip(self.labels, per.tolist()))

    def match_labels(self, logits: np.ndarray) -> Dict[str, bool]:
        output = set_max_true(logits)
        # Shape: (B, classes)]
        return [dict(zip(self.labels, part)) for part in output.tolist()]

    def match_labels_thresholded(
        self, logits: np.ndarray, threshold=0.5
    ) -> Dict[str, bool]:
        output = logits < threshold
        # Shape: (B, classes)]
        return [dict(zip(self.labels, part)) for part in output.tolist()]

    def predict_by_path(self, image_path: str) -> np.ndarray:
        image = load_image(image_path)
        image = tf.expand_dims(image, axis=0)
        image = preprocess_batch(image, self.input_size)
        return self.model.predict(image)

    def predict_by_img(self, image: np.ndarray) -> np.ndarray:
        image = tf.expand_dims(image, axis=0)
        return self.model.predict(image)

    def predict_by_list(self, list_images: List[np.ndarray] | np.ndarray) -> np.ndarray:
        """
        uma lista composta por imagens para ser
        convertida em um batch e processada
        """

        if isinstance(list_images, list):
            list_images = np.stack(list_images)
        else:
            list_images = tf.expand_dims(list_images, axis=0)

        list_images = preprocess_batch(list_images, self.input_size)

        return self.model.predict(list_images)

    def predict_by_array_np(self, array: np.ndarray) -> np.ndarray:
        array = preprocess_batch(array, self.input_size)

        return self.model.predict(array)

    def store_feedback_by_path(self, image_path, true_label):
        """
        para treinar novamente, passa-se as imagens erradas
        e os seus labels verdadeiros
        """
        self.feedback_data.append((preprocess_batch(image_path), true_label))

    def store_feedback_by_img(self, image, true_label):
        self.feedback_data.append((image, true_label))

    def retrain_model(self, epochs=10, batch_size=32):
        if not self.feedback_data:
            return None

        X_train, y_train = zip(*self.feedback_data)
        X_train = np.array(X_train)
        y_train = np.array(y_train)
        print(X_train.shape)
        self.model.compile(
            optimizer="adam",
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        self.model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size)

    def save_model(self, save_path):
        self.model.save(save_path)


import pathlib

_BASE_PATH = pathlib.Path(__file__).parent
_WEIGHTS_PATH = _BASE_PATH.joinpath("weights")

labels = load_json(_WEIGHTS_PATH.joinpath("model_labels.json"))

load_region_model = lambda: ConvolutionalModel(
    _WEIGHTS_PATH.joinpath("region_xray_classification2version.h5"),
    labels["region_xray_classification"],
)

load_pneumonia_model = lambda: ConvolutionalModel(
    _WEIGHTS_PATH.joinpath("pneumonia.keras"), labels["pneumonia_model"]
)

load_modality_model = lambda: ConvolutionalModel(
    _WEIGHTS_PATH.joinpath("modality_model2.keras"),
    labels["modality_model"],
    (112, 112),
)

load_multiple_diseases_model = lambda: ConvolutionalModel(
    _WEIGHTS_PATH.joinpath("multiple_diseases.h5"), labels["multiple_diseases"]
)
