from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


from models import (
    create_diseases,
    create_modality,
    create_region,
    create_ecg_classifier,
)
from decode import base64_to_img
from pydantic import BaseModel
from typing import Dict, List


class ModelInput(BaseModel):
    img: str


CUDA_DEVICES = None  # (0,)
BATCH_SIZE = 2
MAX_LATENCY = 0.1
WORKER_NUM = 1

print("Loading Multiple Diseases Streamer...")
multiple_diseases_streamer = create_diseases(
    CUDA_DEVICES, BATCH_SIZE, MAX_LATENCY, WORKER_NUM
)
print("Finished loading Multiple Diseases Streamer!")

print("Loading ECG Classifier...")
ecg_classifier_streamer = create_ecg_classifier(
    CUDA_DEVICES, BATCH_SIZE, MAX_LATENCY, WORKER_NUM
)
print("Finished loading ECG Classifier!")

print("Loading Modality Classifier...")
modality_streamer = create_modality(CUDA_DEVICES, BATCH_SIZE, MAX_LATENCY, WORKER_NUM)
print("Finished loading Modality Classifier!")

print("Loading Region Classifier...")
region_streamer = create_region(CUDA_DEVICES, BATCH_SIZE, MAX_LATENCY, WORKER_NUM)
print("Finished loading Region Classifier!")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
def homepage(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/status")
def status():
    return {"status": "Service seems to be running!"}


@app.post("/raio-x-doencas")
def read_root(img: ModelInput) -> Dict[str, bool]:
    decoded_img = base64_to_img(img.img)
    output: Dict[str, bool] = multiple_diseases_streamer.predict([decoded_img])[0]
    return output


@app.post("/ecg-descritores")
def read_root(img: ModelInput) -> Dict[str, str | List[str]]:
    decoded_img = base64_to_img(img.img)
    output: Dict[str, str | List[str]] = ecg_classifier_streamer.predict([decoded_img])[
        0
    ]
    return output


@app.post("/modalidade")
def read_root(img: ModelInput) -> Dict[str, bool]:
    decoded_img = base64_to_img(img.img)
    output = modality_streamer.predict([decoded_img])[0]
    return output


@app.post("/regiao")
def read_root(img: ModelInput) -> Dict[str, bool]:
    decoded_img = base64_to_img(img.img)
    output = region_streamer.predict([decoded_img])[0]
    return output
