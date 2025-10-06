from translator import translate
from client import Qwen3OllamaClient, Qwen3OpenAiClient
from matcher import match_keywords
from ctakes import index_texts
from dotenv import load_dotenv

load_dotenv()

CTAKES_PATH = "apache-ctakes-6.0.0-bin"

client = Qwen3OllamaClient(model="qwen3:8b")
original = """RADIOGRAFIA DE TÓRAX PA

Pulmões transparentes.
Circulação pulmonar habitual
Seios costofrênicos livres.
Índice cardio-torácico normal.
Aorta de configuração usual.
Mediastino centrado.
Alterações osteodegenerativas da coluna dorsal e acromioclavicular bilateral."""

translation = translate(client, original)
keywords = index_texts([translation], CTAKES_PATH)[0]

print("Found the following keywords:\n", keywords)
print(
    "Matched CUI to portuguese:\n",
    match_keywords(client, original, translation, keywords),
)
