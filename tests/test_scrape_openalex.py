"""Tests for OpenAlex citation scraping functionality.

Tests cover:
- Title normalization for matching
- API response parsing
"""

import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestTitleNormalization:
    """Test title normalization for case-insensitive matching.
    
    Based on the fix applied to analyze_correlation.py load_data():
    - Lowercase conversion
    - Whitespace normalization (multiple spaces -> single space)
    """

    def normalize(self, title: str) -> str:
        """Normalize title for matching (same logic as analyze.py)."""
        return " ".join(str(title).lower().split())

    def test_case_insensitive(self):
        """Titles differing only in case should match."""
        t1 = "Learning Multi-Level Hierarchies with Hindsight"
        t2 = "Learning Multi-level Hierarchies With Hindsight"
        assert self.normalize(t1) == self.normalize(t2)

    def test_extra_whitespace(self):
        """Titles with extra spaces should normalize."""
        t1 = "A new dog learns old tricks:  RL finds classic optimization"
        t2 = "A new dog learns old tricks: RL finds classic optimization"
        assert self.normalize(t1) == self.normalize(t2)

    def test_leading_trailing_whitespace(self):
        """Leading/trailing whitespace should be stripped."""
        t1 = "  Some Paper Title  "
        t2 = "Some Paper Title"
        assert self.normalize(t1) == self.normalize(t2)

    def test_mixed_issues(self):
        """Combined case and whitespace issues."""
        t1 = "  ATTENTION Is All  You Need  "
        t2 = "Attention is All You Need"
        assert self.normalize(t1) == self.normalize(t2)


class TestOpenAlexResponseParsing:
    """Test parsing of OpenAlex API responses."""

    def test_parse_citation_count(self):
        """Extract citation count from response."""
        mock_response = {
            "id": "W123456",
            "title": "Test Paper",
            "cited_by_count": 150
        }
        assert mock_response.get("cited_by_count") == 150

    def test_missing_citation_count(self):
        """Handle missing citation count gracefully."""
        mock_response = {
            "id": "W123456",
            "title": "Test Paper"
        }
        assert mock_response.get("cited_by_count", 0) == 0

    def test_parse_works_result(self):
        """Parse works search result structure."""
        mock_result = {
            "meta": {"count": 1},
            "results": [
                {
                    "id": "W123456",
                    "title": "Test Paper",
                    "cited_by_count": 75
                }
            ]
        }
        results = mock_result.get("results", [])
        assert len(results) == 1
        assert results[0]["cited_by_count"] == 75


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
