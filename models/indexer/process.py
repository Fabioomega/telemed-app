from .translator import translate
from .client import ClientBase
from .matcher import match_keywords
from .ctakes import index_texts
from .soap import generate_soap
from .common import Keywords, keywords_to_beauty, removed_duplicates
from typing import List, Union


async def process_texts(
    client: ClientBase,
    texts: Union[List[str], str],
    ulms_api_key: str,
    ctakes_path="apache-ctakes-6.0.0-bin",
    use_soap: bool = False,
    do_it_right: bool = True,
):
    if isinstance(texts, str):
        texts = [texts]

    if use_soap:
        texts = [await generate_soap(client, text) for text in texts]

    translations = [await translate(client, text) for text in texts]
    acc = []
    for index, keywords in (
        await index_texts(translations, ctakes_path, ulms_api_key)
    ).items():
        if do_it_right:
            i = 0

            while True:
                if i > 3:
                    raise ValueError("The snomed was fucked!")

                matched_keywords = await match_keywords(
                    client, texts[index], translations[index], keywords
                )

                if not matched_keywords:
                    i += 1
                    continue

                acc.append(keywords_to_beauty(matched_keywords))
                break
        else:
            matched_keywords = await match_keywords(
                client, texts[index], translations[index], keywords
            )

            acc.append(keywords_to_beauty(matched_keywords))

    return {"texts": texts, "medicalTerms": acc}
