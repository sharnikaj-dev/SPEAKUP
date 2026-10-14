"""
retry.py - decides whether a learner's retry actually fixes the mistake.

Idea: compare what the learner originally said with the corrected sentence.
The words that were changed or added are the "key words". A retry passes when
it contains the key words, no longer contains the wrong words, and still looks
like the same sentence. No AI call is needed, so retries are free and instant.
"""
import re
from difflib import SequenceMatcher


def words(text):
    return re.findall(r"[a-z0-9']+", (text or "").lower())


def retry_passed(attempt, learner_text, corrected):
    att, cor, org = words(attempt), words(corrected), words(learner_text)
    if not att or not cor:
        return False
    if att == cor:
        return True

    key, removed = [], []
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, org, cor).get_opcodes():
        if tag in ("replace", "insert"):
            key += cor[j1:j2]
        if tag in ("replace", "delete"):
            removed += org[i1:i2]

    similar = SequenceMatcher(None, att, cor).ratio()
    if not key and not removed:          # only punctuation or capitals differed
        return similar >= 0.9

    has_key_words = all(k in att for k in key)
    dropped_wrong_words = not any(r in att and r not in cor for r in removed)
    return has_key_words and dropped_wrong_words and similar >= 0.6