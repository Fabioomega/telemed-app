import json
from typing import Dict


def load_env(filename: str) -> Dict:
    with open(filename, encoding="utf-8") as file:
        return json.load(file)
