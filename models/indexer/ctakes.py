import glob
import os
import asyncio
import pandas as pd
from typing import NamedTuple, Union, List, Dict
from pathlib import Path
from .common import Keywords, CUIInfo, Spans


class cTakePaths(NamedTuple):
    windows_path: Path
    unix_path: Path


class TablePaths(NamedTuple):
    table_path: Path
    original_number: int


def find_ctakes_shells(ctakes_path: Path) -> cTakePaths:
    w_path: Path
    u_path: Path

    for path in glob.glob(
        str(ctakes_path.joinpath("./**/runClinicalPipeline.*")), recursive=True
    ):
        path = Path(path)
        if path.suffix == ".bat":
            w_path = path
        elif path.suffix == ".sh":
            u_path = path
        else:
            raise ValueError(
                f"What the everliving fuck is a file with the extension {path.suffix}? I don't know how to handle that."
            )

    return cTakePaths(w_path, u_path)


def find_ctakes_home_folder(ctakes_path: Path) -> Path:
    return Path(
        glob.glob(str(ctakes_path.joinpath("./**/bin")), recursive=True)[0]
    ).parent


async def run_ctakes(
    ctakes_path: Union[Path, str],
    input_path: Union[Path, str],
    output_path: Union[Path, str],
    piper_path: Union[Path, str],
    api_key: str,
):
    ctakes_path = Path(ctakes_path)
    input_path = Path(input_path)
    output_path = Path(output_path)
    piper_path = Path(piper_path)

    ctake_shell = Path()
    paths = find_ctakes_shells(ctakes_path)
    home = find_ctakes_home_folder(ctakes_path)

    if os.name == "nt":
        ctake_shell = paths.windows_path
    elif os.name == "posix":
        ctake_shell = paths.unix_path
    else:
        print("[WARNING] Unknown OS. Assuming POSIX-like.")
        ctake_shell = paths.unix_path

    env = os.environ.copy()
    env["CTAKES_HOME"] = str(home.absolute())

    command = (
        f"{ctake_shell.absolute()} "
        f"-i {input_path.absolute()} "
        f"-o {output_path.absolute()} "
        f"--key {api_key} "
        f"--piper {piper_path.absolute()}"
    )

    proc = await asyncio.create_subprocess_shell(
        command,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        print(f"[ERROR] cTAKES failed with code {proc.returncode}")
        print(stderr.decode())
    else:
        print(f"[INFO] cTAKES completed successfully")
        print(stdout.decode())


def get_number(s: str) -> int:
    pos = s.find("_")
    if pos == -1:
        raise ValueError(
            "In the ./input folder there are named files that weren't created by this script! Clean them!"
        )

    return int(s[:pos])


def get_tables_paths(output_path: Path) -> List[TablePaths]:
    return [
        TablePaths(table_path, get_number(table_path.stem))
        for table_path in map(
            Path, glob.glob(str(output_path.joinpath("./bsv_table/*.BSV")))
        )
    ]


def create_file(filepath: Path, content: str):
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content)


def extract_spans(text: str) -> Spans:
    start, end = text.replace(" ", "").split(",")
    return Spans(int(start), int(end))


def extract_keywords(filepath: Path) -> Keywords:
    df = pd.read_csv(filepath, delimiter="|")[
        [
            " Document Text ",
            " Semantic Group ",
            " Span ",
            " Negated ",
            " Uncertain ",
            " CUI ",
        ]
    ].dropna(subset=[" CUI "])

    keywords: Keywords = {}

    for _, row in df.iterrows():
        text = row[" Document Text "].strip()
        keyword_list = keywords.setdefault(text, [])

        keyword_list.append(
            CUIInfo(
                row[" CUI "].split(";"),
                row[" Negated "],
                row[" Uncertain "],
                extract_spans(row[" Span "]),
                row[" Semantic Group "],
            )
        )

    return keywords


async def index_texts(
    texts: List[str], ctakes_path: Union[Path, str], api_key: str
) -> Dict[int, Keywords]:
    os.makedirs("./input", exist_ok=True)
    os.makedirs("./output", exist_ok=True)

    for i, text in enumerate(texts):
        create_file(Path(f"./input/{i}.txt"), text)

    await run_ctakes(ctakes_path, "./input", "./output", "./csvbruh.piper", api_key)

    tables = get_tables_paths(Path("./output"))
    indexed_table = {}
    for table in tables:
        indexed_table[table.original_number] = extract_keywords(table.table_path)

    return indexed_table


if __name__ == "__main__":
    ctakes_path = Path("apache-ctakes-6.0.0-bin")
    text = """Radiology Report – Chest X-ray (PA & Lateral Views)
Study Date: 2025-09-07
Indication: Cough, fever, rule out pneumonia

Findings:
Heart size is within normal limits. Mediastinal contours are unremarkable. Pulmonary vasculature is within normal distribution. No focal consolidation, pleural effusion, or pneumothorax is identified. Lungs are clear bilaterally. Costophrenic angles are sharp. Bony thorax shows no acute osseous abnormalities. Visualized upper abdomen is unremarkable.

No hilar or mediastinal lymphadenopathy. Trachea is midline. No evidence of interstitial markings or alveolar infiltrates. No signs of volume loss or hyperinflation.

Impression:
Normal chest radiograph. No acute cardiopulmonary abnormality."""

    print(index_texts([text], ctakes_path))
    # run_ctakes(ctakes_path, "input", "output", "csvbruh.piper")
