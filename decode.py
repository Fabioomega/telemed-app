import base64
import numpy as np
import cv2


def base64_to_img(encoded_data: str) -> cv2.Mat:
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img
