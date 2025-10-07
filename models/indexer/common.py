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
            "cui": self.cuis,
            "negated": self.negated,
            "uncertain": self.uncertain,
            "spans": [{"start": self.spans.start, "end": self.spans.end}],
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


class PairedText(NamedTuple):
    original: str
    match: str
