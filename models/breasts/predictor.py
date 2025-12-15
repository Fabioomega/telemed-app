from ultralytics import YOLO
import numpy as np
from typing import List, Dict, Any

class BreastDetector:

    def __init__(self, model_path: str):
        self.model = YOLO(model_path)

    def predict(self, images: List[np.ndarray], conf: float = 0.5) -> List[List[Dict[str, Any]]]:

        results = self.model.predict(images, conf=conf)
        
        batch_detections = []

        for result in results:
            image_detections = []
            
            for box in result.boxes:
                detection = {
                    'class': result.names[int(box.cls)],
                    'confidence': float(box.conf),
                    # xywh: centro x, centro y, largura, altura
                    'bbox': box.xywh[0].tolist()
                }
                image_detections.append(detection)
            
            batch_detections.append(image_detections)
        
        return batch_detections