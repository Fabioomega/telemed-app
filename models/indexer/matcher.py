from typing import List, Tuple, Dict
from .client import ClientBase
from .dictionary import create_set_from_text, fix_sentence
from .common import (
    Keywords,
    CUIInfo,
    Spans,
    PairedText,
    strip_cui,
    fix_spans_inplace_regex,
)
import logging
import json

SYS_PROMPT = """You're being given 2 reports, one of them is the original report in portuguese while the other is a translated version in english.
Your job is to correlate important words, or phrases, from the english one to the portuguese one.
You will receive which words and phrases you should correlate.
Your output is a json with each term and their match.

Output Rules:
1. Respond ONLY with the direct correspondences between the terms.
2. Do NOT explain, comment, or add any text besides these pairs.
3. If a term has no match, simply skip it (do NOT write "Explanation", "None", or "Not found").

You'll receive the content as follows:
- Original: {<original text goes here>}
- Translated: {<translated text goes here>}
- Target Words to Correlate: [<english phrase/term1>, <english phrase/term2>, <english phrase/term3>]

JSON Correlated Terms:
{
    "<english phrase/term>": "<portuguese phrase/term>",
    "<english phrase/term2>": "<portuguese phrase/term2>"
    "<english phrase/term3>": "<portuguese phrase/term3>"
}
"""


def create_json_skeleton(keywords: List[str]) -> Dict:
    generic_obj = {"type": "string"}

    json_skeleton = {}

    for keyword in keywords:
        json_skeleton[keyword] = generic_obj

    json_skeleton["required"] = keywords
    return json_skeleton


def first_letter_index(s: str):
    for i, char in enumerate(s):
        if char.isalpha():
            return i
    return -1


def last_letter_index(s: str):
    for i, char in enumerate(reversed(s)):
        if char.isalpha():
            return len(s) - i - 1
    return -1


def first_parenthesis_index(s: str):
    for i, char in enumerate(s):
        if char == "(":
            return i
    return -1


def filter_garbage(s: str) -> str:
    commentary_start = first_parenthesis_index(s)
    if commentary_start != -1:
        s = s[: commentary_start + 1]

    start = first_letter_index(s)
    last = last_letter_index(s)

    return s[start : last + 1]


def format_json_into_desired_answer(text: str) -> List[PairedText]:
    obj = json.loads(text)

    seq = []
    for translated_phrase, original_phrase in obj.items():
        translated_phrase = filter_garbage(translated_phrase)

        seq.append(PairedText(original_phrase.strip(), translated_phrase.strip()))

    return seq


def spell_check_pairs(original_text: str, pairs: List[PairedText]) -> PairedText:
    original_words_set = create_set_from_text(original_text)
    new_pairs = [None for i in range(len(pairs))]

    for i, pair in enumerate(pairs):
        original, match = pair.original, pair.match

        original = fix_sentence(original, original_words_set)

        new_pairs[i] = PairedText(original, match)

    return new_pairs


def fuse_pairs_and_keywords(pairs: List[PairedText], keywords: Keywords) -> Keywords:
    new_keywords = {}
    for pair in pairs:
        original, match = pair.original, pair.match

        if m := keywords.get(match):
            new_keywords[original] = m
        else:
            print(
                f"[WARNING] Match {match} was not found! Probably hallucinated somewhere! Continuing!"
            )

    return new_keywords


async def match_keywords(
    client: ClientBase,
    original_text: str,
    translated_text: str,
    keywords: Keywords,
    verbose: bool = False,
) -> Keywords:
    just_keywords = strip_cui(keywords)

    target_words = str(just_keywords)[1:-1]

    prompt = f"""- Original: [{original_text}]

- Translated: {{{translated_text}}}

- Target Words to Correlate: {{{target_words}}}

JSON Correlated Terms:"""

    pairs = format_json_into_desired_answer(
        await client.async_query(
            prompt,
            SYS_PROMPT,
            verbose=verbose,
            format_obj=create_json_skeleton(just_keywords),
            temperature=0.1,
        )
    )

    pairs = spell_check_pairs(original_text, pairs)

    new_keywords = fuse_pairs_and_keywords(pairs, keywords)

    fix_spans_inplace_regex(original_text, new_keywords)

    return new_keywords
