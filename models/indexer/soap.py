import re
from .client import ClientBase


async def generate_soap(client: ClientBase, texto: str) -> str:
    """
    Gera uma nota SOAP a partir de um texto clínico em português.
    O prompt é em inglês (para melhor compreensão), mas a saída é em português.
    """
    prompt = f"""
You are a clinical assistant that generates SOAP notes in a fixed format.

Tasks:
1) Read ONLY the text provided.
2) Extract and organize the content into SOAP format.
3) Reply ONLY with the SOAP note, in Portuguese (Brazil), following the structure below — no explanations, markdown, or extra text.

Rules:
- Language: Portuguese (Brazil).
- Do NOT invent data. If a section has no information, write: "Sem dados informados."
- Remove HTML, tags, or formatting.
- Follow exactly this structure and blank lines.
- Never translate the labels (keep S, O, A, P exactly as below).

Output format (copy exactly):

S: Subjetivo

<texto subjetivo>

O: Objetivo

<texto objetivo>

A: Avaliação

<texto de avaliação>

P: Plano

<texto de plano>

Input text (in Portuguese):
{texto}
"""

    soap_text = await client.async_query(prompt, "", False)
    return normalize_soap_text(soap_text)


def normalize_soap_text(soap_text: str) -> str:
    """
    Limpa e normaliza o texto SOAP, garantindo espaçamento e títulos corretos.
    """
    s = soap_text.replace("\r\n", "\n").replace("\t", " ")
    s = re.sub(r"[ ]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)

    s = re.sub(r"(^|\n)S:\s*Subjetivo\s*\n+", "\nS: Subjetivo\n\n", s, flags=re.I)
    s = re.sub(r"(^|\n)O:\s*Objetivo\s*\n+", "\nO: Objetivo\n\n", s, flags=re.I)
    s = re.sub(r"(^|\n)A:\s*Avalia[cç]ão\s*\n+", "\nA: Avaliação\n\n", s, flags=re.I)
    s = re.sub(r"(^|\n)P:\s*Plano\s*\n+", "\nP: Plano\n\n", s, flags=re.I)

    return s.strip() + "\n"


if __name__ == "__main__":
    texto = """Paciente relata dor de cabeça e febre há três dias.
    Ao exame físico, temperatura de 38.5°C e leve congestão nasal.
    Diagnóstico provável: rinossinusite viral.
    Prescrito analgésico e repouso domiciliar."""

    soap_text = generate_soap(texto)
    print("==== SOAP TEXT ====")
    print(soap_text)

    html = generate_soap_html(soap_text)
    print("\n==== SOAP HTML ====")
    print(html)
