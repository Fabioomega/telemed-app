from translator import translate
from client import ClientBase
from matcher import match_keywords
from ctakes import index_texts
from typing import List, Union


def index_texts(
    texts: Union[List[str], str],
    client: ClientBase,
    ulms_api_key: str,
    ctakes_path="apache-ctakes-6.0.0-bin",
    do_it_right: bool = True,
):
    if isinstance(texts, str):
        texts = [texts]

    translations = [translate(client, text) for text in texts]
    acc = []
    for index, keywords in index_texts(
        translations, ctakes_path, ulms_api_key, ctakes_path=ctakes_path
    ):
        if do_it_right:
            i = 0
            while True:
                if i > 3:
                    raise ValueError("The snomed was fucked!")

                try:
                    acc.append(
                        match_keywords(
                            client, texts[index], translations[index], keywords
                        )
                    )
                    break
                except Exception as e:

                    print(f"Error happened: {e}")
                    print("Trying again!")
                    i += 1
        else:
            acc.append(
                match_keywords(client, texts[index], translations[index], keywords)
            )

    return acc
