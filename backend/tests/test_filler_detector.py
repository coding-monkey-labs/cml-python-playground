"""Tests for filler word and phrase detection."""

import pytest

from app.services.intelligence.filler_detector import (
    calculate_filler_score,
    detect_fillers_in_segments,
    is_filler_phrase,
)


class TestIsFillerPhrase:
    def test_single_filler_word(self):
        assert is_filler_phrase("um") is True
        assert is_filler_phrase("uh") is True
        assert is_filler_phrase("hmm") is True

    def test_filler_phrase(self):
        assert is_filler_phrase("you know") is True
        assert is_filler_phrase("i mean") is True
        assert is_filler_phrase("sort of") is True

    def test_non_filler(self):
        assert is_filler_phrase("The quick brown fox jumps over the lazy dog") is False
        assert is_filler_phrase("This is an important point") is False

    def test_case_insensitive(self):
        assert is_filler_phrase("Um") is True
        assert is_filler_phrase("UH") is True

    def test_with_punctuation(self):
        assert is_filler_phrase("um,") is True
        assert is_filler_phrase("uh...") is True

    def test_short_filler_segment(self):
        assert is_filler_phrase("um uh") is True

    def test_empty_string(self):
        assert is_filler_phrase("") is False


class TestCalculateFillerScore:
    def test_no_fillers(self):
        score = calculate_filler_score("The weather is beautiful today")
        assert score == 0.0

    def test_all_fillers(self):
        score = calculate_filler_score("um uh um uh")
        assert score == 1.0

    def test_mixed_content(self):
        score = calculate_filler_score("So um the thing is uh we need to um do this")
        assert 0.2 < score < 0.8

    def test_empty_string(self):
        score = calculate_filler_score("")
        assert score == 0.0

    def test_filler_phrases(self):
        score = calculate_filler_score("you know I mean basically actually")
        assert score > 0.3


class TestDetectFillersInSegments:
    def test_annotates_segments(self):
        segments = [
            {"text": "um uh", "start_time": 0.0, "end_time": 1.0},
            {"text": "Hello everyone welcome", "start_time": 1.0, "end_time": 3.0},
        ]
        results = detect_fillers_in_segments(segments)

        assert len(results) == 2
        assert results[0]["is_filler"] is True
        assert results[0]["filler_score"] > 0.5
        assert results[1]["is_filler"] is False
        assert results[1]["filler_score"] < 0.1

    def test_preserves_original_data(self):
        segments = [
            {"text": "test", "start_time": 5.0, "end_time": 6.0, "extra": "data"},
        ]
        results = detect_fillers_in_segments(segments)
        assert results[0]["extra"] == "data"
        assert results[0]["start_time"] == 5.0
