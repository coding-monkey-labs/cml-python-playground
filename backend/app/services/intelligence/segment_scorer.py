"""Segment scoring engine that evaluates transcript chunks on multiple dimensions."""

from dataclasses import dataclass

from app.services.intelligence.filler_detector import calculate_filler_score


@dataclass
class SegmentScores:
    clarity_score: float
    engagement_score: float
    filler_score: float
    retention_risk_score: float


def score_segment(
    text: str,
    duration: float,
    word_count: int,
    confidence: float,
) -> SegmentScores:
    """Score a transcript segment across multiple dimensions.

    All scores are 0.0 to 1.0 where higher = better (except filler_score
    where higher = more fillers).
    """
    filler = calculate_filler_score(text)
    clarity = _calculate_clarity(text, confidence, filler)
    engagement = _calculate_engagement(text, duration, word_count)
    retention_risk = _calculate_retention_risk(filler, clarity, engagement, duration)

    return SegmentScores(
        clarity_score=clarity,
        engagement_score=engagement,
        filler_score=filler,
        retention_risk_score=retention_risk,
    )


def _calculate_clarity(text: str, confidence: float, filler_score: float) -> float:
    """Clarity measures how clean and understandable the segment is."""
    # Base from transcription confidence (normalized from log prob)
    conf_score = min(max((confidence + 1.0) / 1.0, 0.0), 1.0)

    # Penalize for fillers
    clarity = conf_score * (1.0 - filler_score * 0.7)

    # Penalize very short or very long segments
    words = text.split()
    if len(words) < 3:
        clarity *= 0.7
    elif len(words) > 100:
        clarity *= 0.85

    return min(max(clarity, 0.0), 1.0)


def _calculate_engagement(text: str, duration: float, word_count: int) -> float:
    """Engagement estimates how likely viewers are to stay during this segment."""
    if duration <= 0:
        return 0.5

    # Words per minute (ideal: 130-170 WPM)
    wpm = (word_count / duration) * 60
    if 130 <= wpm <= 170:
        pace_score = 1.0
    elif 100 <= wpm <= 200:
        pace_score = 0.7
    else:
        pace_score = 0.4

    # Penalize dead air (low word density)
    if wpm < 30:
        return 0.1

    # Sentence variation (crude heuristic)
    sentences = text.count(".") + text.count("!") + text.count("?")
    variety_score = min(sentences / max(word_count / 20, 1), 1.0)

    engagement = pace_score * 0.6 + variety_score * 0.4
    return min(max(engagement, 0.0), 1.0)


def _calculate_retention_risk(
    filler_score: float,
    clarity_score: float,
    engagement_score: float,
    duration: float,
) -> float:
    """Retention risk: probability that viewers will skip or leave.

    Higher = more likely to cause viewer drop-off.
    """
    risk = 0.0

    # Heavy filler = high risk
    risk += filler_score * 0.4

    # Low clarity = risk
    risk += (1.0 - clarity_score) * 0.3

    # Low engagement = risk
    risk += (1.0 - engagement_score) * 0.2

    # Long segments are riskier
    if duration > 30:
        risk += 0.1

    return min(max(risk, 0.0), 1.0)


def should_remove_segment(scores: SegmentScores, thresholds: dict | None = None) -> bool:
    """Determine if a segment should be removed based on scores."""
    t = thresholds or {
        "filler_threshold": 0.6,
        "clarity_threshold": 0.3,
        "engagement_threshold": 0.2,
        "retention_risk_threshold": 0.7,
    }

    if scores.filler_score >= t["filler_threshold"]:
        return True
    if scores.clarity_score <= t["clarity_threshold"]:
        return True
    if scores.retention_risk_score >= t["retention_risk_threshold"]:
        return True

    return False
