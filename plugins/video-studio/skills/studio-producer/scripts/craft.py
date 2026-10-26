"""Shared craft heuristics for Video Studio helpers (stdlib only).

Kept deliberately small: these are checks a reviewer would make by eye, made
repeatable. They flag likely problems; they do not judge quality.
"""
import re

# Mood words that tell a model or an editor nothing concrete on their own.
VAGUE = {
    "en": {"cinematic", "epic", "dynamic", "engaging", "stunning", "beautiful", "amazing",
           "awesome", "cool", "modern", "sleek", "high-quality", "professional", "viral", "eye-catching"},
    "id": {"sinematik", "keren", "menarik", "bagus", "estetik", "kekinian", "mewah", "profesional", "viral", "epik"},
}
# Planning pace only; real word timestamps replace it after voicing.
WORDS_PER_SECOND = {"en": 2.6, "id": 2.2}
CAPTION_LINE = {"en": 42, "id": 38}
AUDIO_TAG = re.compile(r"\[[^\]]+\]")


def vague_words(text, languages=("en", "id")):
    """Return vague mood words found in text, in order of appearance."""
    found = []
    for token in re.findall(r"[\w-]+", text.casefold()):
        if any(token in VAGUE[lang] for lang in languages) and token not in found:
            found.append(token)
    return found


def spoken(text):
    """Text as it will be spoken: audio tags removed, whitespace collapsed."""
    return " ".join(AUDIO_TAG.sub(" ", text).split())


def word_count(text):
    return len(re.findall(r"[\w'’-]+", spoken(text)))


def planned_seconds(text, language):
    return word_count(text) / WORDS_PER_SECOND[language]
