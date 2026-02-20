"""Filler word and phrase detection using rule-based and pattern matching."""

import re

# Common filler words and phrases
FILLER_WORDS = {
    "um",
    "uh",
    "uhh",
    "umm",
    "ummm",
    "er",
    "err",
    "ah",
    "ahh",
    "hmm",
    "hmmm",
    "mhm",
    "huh",
}

FILLER_PHRASES = {
    "you know",
    "i mean",
    "like",
    "sort of",
    "kind of",
    "basically",
    "actually",
    "literally",
    "right",
    "so yeah",
    "you know what i mean",
    "at the end of the day",
    "to be honest",
    "if you will",
    "as it were",
    "in a sense",
    "more or less",
    "if that makes sense",
}

# Repetition patterns
REPETITION_PATTERN = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)

# Stuttering patterns (e.g., "I I I", "the the")
STUTTER_PATTERN = re.compile(r"\b(\w+)(\s+\1){2,}\b", re.IGNORECASE)


def is_filler_phrase(text: str) -> bool:
    """Check if the entire segment is primarily a filler phrase."""
    cleaned = text.strip().lower()
    cleaned = re.sub(r"[^\w\s]", "", cleaned)

    # Direct match
    if cleaned in FILLER_WORDS or cleaned in FILLER_PHRASES:
        return True

    # Short segment that's mostly filler
    words = cleaned.split()
    if len(words) <= 3:
        filler_count = sum(1 for w in words if w in FILLER_WORDS)
        if filler_count >= len(words) * 0.5:
            return True

    return False


def calculate_filler_score(text: str) -> float:
    """Calculate filler density score for a text segment.

    Returns a score between 0.0 (no fillers) and 1.0 (all fillers).
    """
    cleaned = text.strip().lower()
    words = cleaned.split()
    if not words:
        return 0.0

    filler_count = 0

    # Count filler words
    for word in words:
        clean_word = re.sub(r"[^\w]", "", word)
        if clean_word in FILLER_WORDS:
            filler_count += 1

    # Count filler phrases
    for phrase in FILLER_PHRASES:
        occurrences = cleaned.count(phrase)
        if occurrences > 0:
            phrase_word_count = len(phrase.split())
            filler_count += occurrences * phrase_word_count

    # Check for repetition
    repetitions = REPETITION_PATTERN.findall(cleaned)
    filler_count += len(repetitions)

    # Check for stuttering
    stutters = STUTTER_PATTERN.findall(cleaned)
    filler_count += len(stutters) * 2

    return min(filler_count / len(words), 1.0)


def detect_fillers_in_segments(
    segments: list[dict],
) -> list[dict]:
    """Analyze a list of transcript segments for filler content.

    Each segment should have: text, start_time, end_time
    Returns segments annotated with filler information.
    """
    results = []
    for seg in segments:
        text = seg.get("text", "")
        score = calculate_filler_score(text)
        results.append(
            {
                **seg,
                "filler_score": score,
                "is_filler": is_filler_phrase(text),
                "filler_words_found": [
                    w
                    for w in text.lower().split()
                    if re.sub(r"[^\w]", "", w) in FILLER_WORDS
                ],
            }
        )
    return results
