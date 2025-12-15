def detect_breasts(image_path: str, model) -> list:
    """
    Perform YOLO breast detection on an image.
    
    Args:
        image_path: Path to the input image
        model: Trained YOLO model object
    
    Returns:
        List of detections with probabilities in format:
        [{'class': str, 'confidence': float, 'bbox': [x, y, w, h]}, ...]
    """
    results = model.predict(image_path, conf=0.5)
    
    detections = []
    for result in results:
        for box in result.boxes:
            detection = {
                'class': result.names[int(box.cls)],
                'confidence': float(box.conf),
                'bbox': box.xywh[0].tolist()
            }
            detections.append(detection)
    
    return detections