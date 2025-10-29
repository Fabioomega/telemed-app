import regex as re
from typing import NamedTuple, Union, List, Dict, TypedDict, Tuple


CUI = str
EXPRESSION = str


class Spans(NamedTuple):
    start: int
    end: int


class CUIInfo(NamedTuple):
    cuis: List[CUI]
    negated: bool
    uncertain: bool
    spans: Spans
    semantic_group: str

    def to_dict(self):
        return {
            "cuis": self.cuis,
            "negated": self.negated,
            "uncertain": self.uncertain,
            "spans": {"start": self.spans.start, "end": self.spans.end},
            "semanticGroup": self.semantic_group,
        }


Keywords = Dict[EXPRESSION, List[CUIInfo]]


def strip_cui(keywords: Keywords) -> List[str]:
    return list(keywords.keys())


def keywords_to_beauty(keywords: Keywords) -> Dict:
    new_dict = {}
    for key, cuis in keywords.items():
        new_dict[key] = [cui.to_dict() for cui in cuis]

    return new_dict


def dict_to_CUIInfo(c: Dict):
    return CUIInfo(
        cuis=c["cuis"],
        negated=c["negated"],
        uncertain=c["uncertain"],
        spans=Spans(
            c["spans"]["start"],
            c["spans"]["end"],
        ),
        semantic_group=c["semanticGroup"],
    )


def beauty_to_keywords(d: Dict) -> Keywords:
    new_dict = {}
    for key, d in d.items():
        new_dict[key] = [dict_to_CUIInfo(d) for d in d]

    return new_dict


def removed_duplicates(keywords: Keywords) -> Dict:
    new_dict = {}
    for key, cuis in keywords.items():
        all_semantic_groups = {}
        for cui in cuis:
            all_semantic_groups[cui.semantic_group] = 0

        filtered_cuis = []
        for cui in cuis:
            sg = cui.semantic_group
            if all_semantic_groups[sg] == 0:
                all_semantic_groups[sg] = 1
                filtered_cuis.append(cui)

            continue

        new_dict[key] = filtered_cuis

    return new_dict


def fix_spans_inplace_regex(
    origin: str,
    keywords: Keywords,
    use_lowercase: bool = True,
    overlapped: bool = True,
    remove_not_found: bool = True,
):
    """
    Updates the `spans` field of each CUIInfo entry in `keywords` by finding exact matches
    of the keyword expressions in the `origin` text using regular expressions.

    The operation is performed in-place.

    Args:
        origin (str): The original text in which to search for keyword expressions.
        keywords (Keywords): A dictionary mapping keyword expressions to a list of `CUIInfo` objects.
        use_lowercase (bool, optional): If True, all matches happen in lowercase.
        overlapped (bool, optional): If True, allows overlapping matches using regex.
            If False, only non-overlapping matches are found. Defaults to True.
        remove_not_found (bool, optional): If True, removes keywords not matched in the origin text.

    Note:
        - When `overlapped` is False and the number of CUIInfo entries for a keyword exceeds the number of matches found,
          the unmatched entries will remain unchanged and no warning will be printed BE CAREFUL!.
        - This function assumes that the order of CUIInfo objects corresponds to the order in which the keyword appears
          in the `origin` text.
    """
    last_position = {}
    keyword_keys = keywords.keys()

    if use_lowercase:
        keyword_keys = [k.lower() for k in keywords.keys()]
        origin = origin.lower()

    pattern = re.compile("|".join(re.escape(k) for k in keyword_keys))

    for match in pattern.finditer(origin, overlapped=overlapped):
        matched_text = match.group()

        last_position.setdefault(matched_text, 0)
        if len(origin) > last_position[matched_text]:
            index = last_position[matched_text]
            group = keywords[matched_text][index]
            pos = match.start()

            keywords[matched_text][index] = group._replace(
                spans=Spans(pos, pos + len(matched_text))
            )
            last_position[matched_text] += 1
        elif not overlapped:
            print(f"[WARNING] The term '{matched_text}' was out of bounds!")
            continue

    keywords_text = set(keyword_keys)
    matches = set(last_position.keys())
    for not_found_matches in keywords_text - matches:
        print(f"[WARNING] The term '{not_found_matches}' was not found!")
        if remove_not_found:
            del keywords[not_found_matches]


class PairedText(NamedTuple):
    original: str
    match: str
