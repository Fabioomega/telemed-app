from ultralytics import YOLO
from typing import List, Dict, Any

class BreastDetector:

    def __init__(self, model_path: str):

        self.model = YOLO(model_path)

    def predict(self, image_path: str, conf: float = 0.5) -> List[Dict[str, Any]]:

        results = self.model.predict(image_path, conf=conf)
        
        detections = []
        for result in results:
            for box in result.boxes:
                detection = {
                    'class': result.names[int(box.cls)],
                    'confidence': float(box.conf),
                    #centro x, centro y, largura e altura
                    'bbox': box.xywh[0].tolist()
                }
                detections.append(detection)
        
        return detections