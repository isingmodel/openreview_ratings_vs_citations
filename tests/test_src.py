"""Tests for shared logic in scripts/src.py."""

import sys
from pathlib import Path

import pytest
import numpy as np
import pandas as pd

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from src import parse_rating_data, calculate_weighted_rating, normalize_title


class TestParseRatingData:
    """Test parsing of rating data from various formats."""

    def test_parse_json_string(self):
        """Parse JSON string of list of dicts."""
        data = '[{"rating": 8, "confidence": 4}, {"rating": 6, "confidence": 3}]'
        result = parse_rating_data(data)
        assert len(result) == 2
        assert result[0]["rating"] == 8
        assert result[1]["rating"] == 6

    def test_parse_list_of_ints(self):
        """Parse legacy list of integers."""
        data = [8, 6, 7]
        result = parse_rating_data(data)
        assert len(result) == 3
        # Should default confidence to 4
        assert result[0] == {"rating": 8, "confidence": 4}

    def test_parse_list_of_dicts(self):
        """Pass through list of dicts."""
        data = [{"rating": 8, "confidence": 4}]
        result = parse_rating_data(data)
        assert result == data

    def test_invalid_input(self):
        """Handle invalid input gracefully."""
        assert parse_rating_data(None) == []
        assert parse_rating_data("invalid json") == []
        assert parse_rating_data([]) == []


class TestCalculateWeightedRating:
    """Test confidence-weighted rating calculation."""

    def test_weighted_average(self):
        """Calculate weighted average."""
        ratings = [
            {"rating": 10, "confidence": 5}, # 50
            {"rating": 5, "confidence": 1},  # 5
        ]
        # (50 + 5) / (5 + 1) = 55 / 6 = 9.166...
        result = calculate_weighted_rating(ratings)
        assert result == pytest.approx(9.1666666)

    def test_missing_confidence(self):
        """Handle missing confidence (default to 1)."""
        ratings = [
            {"rating": 10}, # weight 1 -> 10
            {"rating": 5, "confidence": 1}, # 5
        ]
        # (10 + 5) / (1 + 1) = 15 / 2 = 7.5
        result = calculate_weighted_rating(ratings)
        assert result == 7.5

    def test_empty_input(self):
        """Handle empty input."""
        assert calculate_weighted_rating([]) is None


class TestNormalizeTitle:
    """Test title normalization."""

    def test_case_insensitive(self):
        """Titles differing only in case should match."""
        t1 = "Learning Multi-Level Hierarchies with Hindsight"
        t2 = "Learning Multi-level Hierarchies With Hindsight"
        assert normalize_title(t1) == normalize_title(t2)

    def test_extra_whitespace(self):
        """Titles with extra spaces should normalize."""
        t1 = "A new dog learns old tricks:  RL finds classic optimization"
        t2 = "A new dog learns old tricks: RL finds classic optimization"
        assert normalize_title(t1) == normalize_title(t2)

    def test_leading_trailing_whitespace(self):
        """Leading/trailing whitespace should be stripped."""
        t1 = "  Some Paper Title  "
        t2 = "Some Paper Title"
        assert normalize_title(t1) == normalize_title(t2)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
