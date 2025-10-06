from client import ClientBase
from typing import List, Tuple
from dictionary import create_set_from_text, fix_sentence
from common import Keywords, CUIInfo, Spans, PairedText, strip_cui

EXAMPLE = """Example:
- Original: {Raios X de Tórax

Arcos costais aparentemente íntegros
Ausência de condensações alveolares
Seios costofrênicos livres
Mediastino sem alterações
Área cardíaca normal
Circulação pulmonar preservada}
- Translated: {Chest X-Ray

Rib arches apparently intact
No alveolar consolidations
Costophrenic angles clear
Mediastinum without alterations
Normal cardiac silhouette
Pulmonary circulation preserved}
- Target Words to Correlate: ["Raios X de Tórax", "Arcos costais", "Mediastino"]

Answer:
Chest X-Ray - Raios X de Tórax
Rib arches - Arcos costais
Mediastinum - Mediastino"""

_SYS_PROMPT = """You're being given 2 reports, one of them is the original report in portuguese while the other is a translated version in english.
Your job is to correlate important words, or phrases, from the english one to the portuguese one.
The correlated words may contain a prelude or epilogue that is denoted between [].
The prelude or epilogue should NOT appear in the answer; it's just there to help you correlate between sentences better.
You will receive which words and phrases you should correlate.
You'll receive the content as follows:
- Original: {<original text goes here>}
- Translated: {<translated text goes here>}
- Target Words to Correlate: {[prelude]<english phrase/term1>[epilogue], <english phrase/term2>, [prologue]<english phrase/term3>}

Correlated Terms:
<english phrase/term> - <portuguese phrase/term>
<english phrase/term2> - <portuguese phrase/term>
<english phrase/term3> - <portuguese phrase/term>
"""

SYS_PROMPT = """You're being given 2 reports, one of them is the original report in portuguese while the other is a translated version in english.
Your job is to correlate important words, or phrases, from the english one to the portuguese one.
You will receive which words and phrases you should correlate. Do not add any commentary.
You'll receive the content as follows:
- Original: {<original text goes here>}
- Translated: {<translated text goes here>}
- Target Words to Correlate: {<english phrase/term1>, <english phrase/term2>, <english phrase/term3>}

Correlated Terms:
<english phrase/term> - <portuguese phrase/term>
<english phrase/term2> - <portuguese phrase/term>
<english phrase/term3> - <portuguese phrase/term>
"""


# def unravel_position(words: List[List[str]], position: int) -> Tuple[int, int]:
#     for outer, sentence in enumerate(words):
#         for inner, word in enumerate(sentence[:-1]):
#             if position < len(word):
#                 return (outer, inner)
#             position -= len(word)
#             position -= 1  # Spaces or Tabs

#         if position < len(sentence[-1]):
#             return (outer, inner)

#         position -= len(word)
#         position -= 1  # Newlines
#     raise ValueError(
#         "The unraveling was not possible because the position references data outside words!"
#     )


# def strip_cui_and_format_old(keywords: Keywords, translated_text: str) -> List[str]:
#     words = [line.split() for line in translated_text.split("\n")]
#     seq = [None for _ in range(len(keywords))]

#     for i, (expression, cuis) in enumerate(keywords.items()):
#         for cui in cuis:
#             start, end = (
#                 unravel_position(words, cui.spans.start),
#                 unravel_position(words, cui.spans.end - 1),
#             )

#             prelude = ""
#             if start[1] != 0:
#                 prelude = f"[{words[start[0]][start[1] - 1]} ]"

#             epilogue = ""
#             if end[1] != len(words[end[0]]) - 1:
#                 epilogue = f"[ {words[end[0]][end[1] - 1]}]"

#             seq[i] = f"{prelude}{expression}{epilogue}"

#     return seq


# def rfind_word(text: str) -> int:
#     if not text:
#         return -1

#     i = len(text) - 1

#     # Skip trailing spaces and newlines
#     while i >= 0 and text[i] in {" ", "\n"}:
#         i -= 1

#     if i < 0:
#         return -1

#     # Find the start of the word
#     while i >= 0 and text[i] not in {" ", "\n"}:
#         i -= 1

#     start = i + 1

#     return start


# def find_word(text: str) -> int:
#     if not text:
#         return -1

#     i = 0

#     # Skip trailing spaces and newlines
#     while i >= 0 and text[i] in {" ", "\n"}:
#         i -= 1

#     if i < 0:
#         return -1

#     # Find the start of the word
#     while i >= 0 and text[i] not in {" ", "\n"}:
#         i -= 1

#     start = i + 1

#     return start


# def strip_cui_and_format(keywords: Keywords, translated_text: str) -> List[str]:
#     seq = [None for _ in range(len(keywords))]

#     for i, (expression, cuis) in enumerate(keywords.items()):
#         cui = cuis[0]
#         start, end = cui.spans.start, cui.spans.end

#         prelude_index = rfind_word(translated_text[:start])
#         epilogue_index = find_word(translated_text[end:])

#         prelude = ""
#         if prelude_index != -1:
#             prelude = f"[{translated_text[prelude_index:start]}]"

#         epilogue = ""
#         if epilogue_index != -1:
#             epilogue = f"[{translated_text[end:epilogue_index]}]"

#         seq[i] = f"{prelude}{expression}{epilogue}"

#     return seq


def first_letter_index(s: str):
    for i, char in enumerate(s):
        if char.isalpha():
            return i
    return -1


def first_parenthesis_index(s: str):
    for i, char in enumerate(s):
        if char == "(":
            return i
    return -1


def format_desired_answer(text: str) -> List[PairedText]:
    header = "correlated terms:"

    pos = text.lower().find(header)
    if pos != -1:
        text = text[pos + len(header) :]

    seq = []
    for line in text.split("\n"):
        if not line or line.isspace():
            continue

        line = line[first_letter_index(line) :]

        translated_phrase, original_phrase = line.split(" - ")
        commentary_index = first_parenthesis_index(original_phrase)

        if commentary_index != -1:
            original_phrase = original_phrase[: commentary_index + 1]

        seq.append(PairedText(original_phrase.strip(), translated_phrase.strip()))

    return seq


def spell_check_pairs(
    original_text: str, keywords: Keywords, pairs: List[PairedText]
) -> PairedText:
    original_words_set = create_set_from_text(original_text)
    str_keywords = list(keywords.keys())

    new_pairs = [None for i in range(len(pairs))]

    for i, pair in enumerate(pairs):
        original, match = pair.original, pair.match

        original = fix_sentence(original, original_words_set)
        match = fix_sentence(match, str_keywords, match_whole=True)

        new_pairs[i] = PairedText(original, match)

    return new_pairs


def fix_spans_inplace(original: str, keywords: Keywords) -> Keywords:
    raise NotImplementedError("Spans are not correct as of yet!")

    original = original.lower()

    repeated_offsets = {}
    for original_sentence in keywords.keys():
        sentence = original_sentence.lower()

        offset = 0
        if f := repeated_offsets.get(sentence):
            offset = f

        start = original.find(sentence[offset:])
        if start == -1:
            print(
                f"[WARNING] The fucking ai just hallucinated '{original_sentence}' or it's a spelling mistake. Skipping!"
            )
            del keywords[original_sentence]
            continue

        end = start + len(sentence[offset:])

        keywords[original_sentence] = keywords[original_sentence]._replace(
            spans=Spans(start, end)
        )

        repeated_offsets[sentence] = end

    return keywords


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


def match_keywords(
    client: ClientBase,
    original_text: str,
    translated_text: str,
    keywords: List[Keywords],
    verbose: bool = False,
) -> Keywords:

    target_words = str(strip_cui(keywords))[1:-1]

    prompt = f"""- Original: {{{original_text}}}
- Translated: {{{translated_text}}}
- Target Words to Correlate: {{{target_words}}}

Correlated Terms:"""

    pairs = format_desired_answer(client.query(prompt, SYS_PROMPT, verbose=verbose))

    pairs = spell_check_pairs(original_text, keywords, pairs)

    return fuse_pairs_and_keywords(pairs, keywords)
