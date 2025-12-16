import cv2
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import (
    create_diseases,
    create_modality,
    create_region,
    create_ecg_classifier,
    create_fracture,
)

from decode import base64_to_img
from pydantic import BaseModel
from typing import Dict, List
from environment_loader import Environment

from models.indexer.client import Qwen3OllamaClient, Qwen3OpenAiClient
from models.indexer import index_texts, Keywords


class ModelInput(BaseModel):
    img: str


class IndexInput(BaseModel):
    text: str
    use_soap: bool


CUDA_DEVICES = None  # (0,)
BATCH_SIZE = 2
MAX_LATENCY = 0.1
WORKER_NUM = 1

multiple_diseases_streamer = create_diseases(
    CUDA_DEVICES, BATCH_SIZE, MAX_LATENCY, WORKER_NUM
)

ecg_classifier_streamer = create_ecg_classifier(
    CUDA_DEVICES, BATCH_SIZE, MAX_LATENCY, WORKER_NUM
)

modality_streamer = create_modality(CUDA_DEVICES, BATCH_SIZE, MAX_LATENCY, WORKER_NUM)

region_streamer = create_region(CUDA_DEVICES, BATCH_SIZE, MAX_LATENCY, WORKER_NUM)

fracture_streamer = create_fracture(CUDA_DEVICES, BATCH_SIZE, MAX_LATENCY, WORKER_NUM)


env = Environment("env.json")
client = Qwen3OllamaClient()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
def homepage(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/ecg")
def homepage(request: Request):
    return templates.TemplateResponse(request=request, name="ecg-demo.html")


@app.get("/radio")
def homepage(request: Request):
    return templates.TemplateResponse(request=request, name="radiology-demo.html")


@app.get("/snow")
def homepage(request: Request):
    return templates.TemplateResponse(request=request, name="snomed-demo.html")


@app.get("/status")
def status():
    return {"status": "Service seems to be running!"}


@app.post("/raio-x-doencas")
def diseases(img: ModelInput) -> Dict[str, bool]:
    decoded_img = base64_to_img(img.img)
    output: Dict[str, bool] = multiple_diseases_streamer.predict([decoded_img])[0]
    return output


@app.post("/ecg-descritores")
def read_route(img: ModelInput) -> Dict[str, str | List[str]]:
    decoded_img = base64_to_img(img.img)

    from models.ecg.model_api import load_clip_model

    direct_model = load_clip_model()
    output: Dict[str, str | List[str]] = direct_model.predict(
        [decoded_img], threshold=0.2
    )[0]
    return output


@app.post("/modalidade")
def modality(img: ModelInput) -> Dict[str, bool]:
    decoded_img = base64_to_img(img.img)
    output = modality_streamer.predict([decoded_img])[0]
    return output


@app.post("/regiao")
def region(img: ModelInput) -> Dict[str, bool]:
    decoded_img = base64_to_img(img.img)
    output = region_streamer.predict([decoded_img])[0]
    return output


@app.post("/fracture")
def region(img: ModelInput) -> Dict[str, bool]:
    decoded_img = base64_to_img(img.img)
    img_matrix = fracture_streamer.predict([decoded_img])[0]
    success, encoded = cv2.imencode(".png", img_matrix)

    return Response(content=encoded.tobytes(), media_type="image/png")


@app.post("/index")
async def index(inp: IndexInput):
    indexed = await index_texts(
        client, inp.text, env.get("SNOMED_API_KEY"), use_soap=inp.use_soap
    )

    return {"text": indexed["texts"][0], "medicalTerms": indexed["medicalTerms"][0]}
