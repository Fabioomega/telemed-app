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
from completion import LLMOllama, LLMOpenAI, Block
from env import load_env


class ModelInput(BaseModel):
    img: str


class LLMCompleteInput(BaseModel):
    start: str
    img: str


class LLMOutput(BaseModel):
    generated_text: str


env = load_env("env.json")

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

if env.get("use-ollama"):
    BACKEND = LLMOllama
else:
    BACKEND = LLMOpenAI

llm = BACKEND(
    env.get("host"),
    env.get("prompt"),
    env.get("model"),
    env.get("image_token"),
    env.get("base_template"),
    Block(env.get("prompt_start_user"), env.get("prompt_end_user")),
    Block(env.get("prompt_start_assistant"), env.get("prompt_end_assistant")),
)

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
    output: Dict[str, str | List[str]] = ecg_classifier_streamer.predict([decoded_img])[
        0
    ]
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


@app.post("/gerar-laudo")
async def gerar_report(inp: ModelInput) -> LLMOutput:
    return LLMOutput(generated_text=await llm.generate(inp.img))


@app.post("/completar-laudo")
async def complete_report(inp: LLMCompleteInput) -> LLMOutput:
    return LLMOutput(generated_text=await llm.complete(inp.start, inp.img))
