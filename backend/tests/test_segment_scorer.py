"""Tests for segment scoring logic."""

import pytest

from app.services.intelligence.segment_scorer import (
    SegmentScores,
    score_segment,
    should_remove_segment,
)


class TestScoreSegment:
    def test_clean_segment(self):
        scores = score_segment(
            text="Welcome to today's video. We'll be discussing Python programming.",
            duration=5.0,
            word_count=9,
            confidence=-0.3,
        )
        assert scores.clarity_score > 0.3
        assert scores.filler_score < 0.2

    def test_filler_heavy_segment(self):
        scores = score_segment(
            text="um uh you know like basically um",
            duration=3.0,
            word_count=7,
            confidence=-0.5,
        )
        assert scores.filler_score > 0.5
        assert scores.clarity_score < 0.5

    def test_dead_air_segment(self):
        scores = score_segment(
            text="okay",
            duration=10.0,
            word_count=1,
            confidence=-0.8,
        )
        assert scores.engagement_score < 0.3

    def test_good_pace_segment(self):
        # ~150 WPM (ideal range)
        text = " ".join(["word"] * 25)
        scores = score_segment(
            text=text,
            duration=10.0,
            word_count=25,
            confidence=-0.2,
        )
        assert scores.engagement_score > 0.3

    def test_scores_bounded(self):
        scores = score_segment(
            text="um " * 50,
            duration=0.1,
            word_count=50,
            confidence=-2.0,
        )
        assert 0.0 <= scores.clarity_score <= 1.0
        assert 0.0 <= scores.engagement_score <= 1.0
        assert 0.0 <= scores.filler_score <= 1.0
        assert 0.0 <= scores.retention_risk_score <= 1.0


class TestShouldRemoveSegment:
    def test_high_filler_removed(self):
        scores = SegmentScores(
            clarity_score=0.5,
            engagement_score=0.5,
            filler_score=0.8,
            retention_risk_score=0.5,
        )
        assert should_remove_segment(scores) is True

    def test_low_clarity_removed(self):
        scores = SegmentScores(
            clarity_score=0.2,
            engagement_score=0.5,
            filler_score=0.1,
            retention_risk_score=0.5,
        )
        assert should_remove_segment(scores) is True

    def test_high_retention_risk_removed(self):
        scores = SegmentScores(
            clarity_score=0.5,
            engagement_score=0.5,
            filler_score=0.1,
            retention_risk_score=0.8,
        )
        assert should_remove_segment(scores) is True

    def test_good_segment_kept(self):
        scores = SegmentScores(
            clarity_score=0.8,
            engagement_score=0.7,
            filler_score=0.1,
            retention_risk_score=0.2,
        )
        assert should_remove_segment(scores) is False

    def test_custom_thresholds(self):
        scores = SegmentScores(
            clarity_score=0.5,
            engagement_score=0.5,
            filler_score=0.4,
            retention_risk_score=0.5,
        )
        # Default thresholds: should not remove
        assert should_remove_segment(scores) is False
        # Strict thresholds: should remove
        strict = {
            "filler_threshold": 0.3,
            "clarity_threshold": 0.6,
            "engagement_threshold": 0.6,
            "retention_risk_threshold": 0.4,
        }
        assert should_remove_segment(scores, strict) is True
