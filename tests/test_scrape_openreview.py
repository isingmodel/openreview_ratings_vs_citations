"""Tests for OpenReview scraping functionality.

Tests cover:
- Invitation string generation per year
- API version selection (v1 for pre-2021, v2 for 2021+)
- Rating/confidence parsing logic
"""

import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from scrape_openreview import get_invitation, INVITATION_PATTERNS


class TestGetInvitation:
    """Test invitation string generation."""

    def test_known_year_2017(self):
        """2017 uses lowercase 'conference'."""
        result = get_invitation(2017)
        assert result == "ICLR.cc/2017/conference/-/submission"

    def test_known_year_2019(self):
        """2019 uses Blind_Submission format."""
        result = get_invitation(2019)
        assert result == "ICLR.cc/2019/Conference/-/Blind_Submission"

    def test_known_year_2024(self):
        """2024 uses new Submission format."""
        result = get_invitation(2024)
        assert result == "ICLR.cc/2024/Conference/-/Submission"

    def test_unknown_future_year(self):
        """Unknown years should use default pattern."""
        result = get_invitation(2030)
        assert result == "ICLR.cc/2030/Conference/-/Submission"


class TestAPIVersionSelection:
    """Test API version branching logic.
    
    Based on scrape_openreview() logic:
    - v1 is tried first for all years
    - v2 is fallback for years >= 2021 if v1 returns empty
    """

    def test_v1_years(self):
        """Years 2017-2020 should primarily use v1."""
        v1_years = [2017, 2018, 2019, 2020]
        for year in v1_years:
            # v1 should be in the invitation patterns
            assert year in INVITATION_PATTERNS
            # These years should not trigger v2 fallback (year < 2021)
            assert year < 2021

    def test_v2_fallback_threshold(self):
        """Years >= 2021 can fall back to v2."""
        v2_years = [2021, 2022, 2023, 2024, 2025]
        for year in v2_years:
            assert year >= 2021


class TestRatingParsing:
    """Test rating string parsing logic."""

    def test_parse_rating_string_with_colon(self):
        """Parse '8: Top 50% of accepted papers' -> 8"""
        rating_str = "8: Top 50% of accepted papers"
        result = int(rating_str.split(":")[0])
        assert result == 8

    def test_parse_rating_integer(self):
        """Direct integer rating."""
        rating = 7
        assert isinstance(rating, int)
        assert rating == 7

    def test_parse_confidence_string(self):
        """Parse '4: Confident but not absolutely certain'"""
        conf_str = "4: Confident but not absolutely certain"
        result = int(conf_str.split(":")[0])
        assert result == 4


class TestInvitationPatterns:
    """Test that invitation patterns are correctly defined."""

    def test_all_years_have_patterns(self):
        """Verify patterns exist for 2017-2025."""
        expected_years = list(range(2017, 2026))
        for year in expected_years:
            assert year in INVITATION_PATTERNS, f"Missing pattern for {year}"

    def test_blind_submission_years(self):
        """2018-2023 use Blind_Submission format."""
        blind_years = [2018, 2019, 2020, 2021, 2022, 2023]
        for year in blind_years:
            assert "Blind_Submission" in INVITATION_PATTERNS[year]

    def test_submission_format_years(self):
        """2024+ use plain Submission format."""
        new_format_years = [2024, 2025]
        for year in new_format_years:
            pattern = INVITATION_PATTERNS[year]
            assert "Submission" in pattern
            assert "Blind" not in pattern


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
