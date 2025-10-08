from typing import List
from rapidfuzz import fuzz, process, utils
from .common import Keywords


def create_set_from_text(text: str) -> List[str]:
    text = utils.default_process(text)

    return list(set(text.split()))


def fix_part(part: str, words_set: List[str], threshold: float = 0.6) -> str:
    choice = process.extractOne(
        part, words_set, scorer=fuzz.QRatio, processor=utils.default_process
    )

    recommended_word, score = (words_set[choice[-1]], choice[1])
    if score >= threshold:
        return recommended_word

    return part


def fix_sentence(
    sentence: str,
    words_set: List[str],
    threshold: float = 0.6,
    match_whole: bool = False,
) -> str:
    if match_whole:
        return fix_part(sentence, words_set, threshold)

    parts = sentence.split()
    return " ".join([fix_part(part, words_set, threshold) for part in parts])


if __name__ == "__main__":
    text = """While others practiced their fire-breathing on boulders and trees, Flame tiptoed through meadows, gently sniffing daisies, tulips, and especially peonies — his favorite. His fire was so gentle that it never burned anything — it just gave the flowers a little warmth to help them grow.
One day, while tending his garden, Flame heard a tiny sniffle. Behind a bush, he found a little girl named Elia, crying because her village's crops wouldn't grow.
“They're all frozen,” she said, wiping her nose. “We'll have no food for winter.”
Flame tilted his head, a spark of an idea lighting in his heart.
He flew with her to the village and, with the softest breath of his warm fire, melted the frost gently from the soil. The villagers watched in awe as their plants began to lift their heads again.
From that day on, Flame became the village's secret friend. He visited every morning to warm the soil and whisper encouragement to the seedlings. In return, the villagers planted a garden just for him — a sea of color where Flame would lie for hours, surrounded by flowers and laughter.
And though he had no pile of gold or fearsome roar, Flame was the happiest dragon in the world — because he had helped something grow.
"""

    sentece = "thau frazen"

    word_set = create_set_from_text(text)

    print(fix_sentence(sentece, word_set))
