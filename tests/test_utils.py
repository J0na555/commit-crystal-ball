import pytest

from crystal_ball.detector._utils import Finding, get_line_snippet


class TestFinding:
    """Tests for Finding dataclass."""

    def test_finding_creation(self):
        f = Finding(
            check_id="test",
            message="test message",
            line=1,
            snippet="code",
            suggested_fix="fix it",
            severity="high",
        )
        assert f.check_id == "test"
        assert f.message == "test message"
        assert f.line == 1
        assert f.snippet == "code"
        assert f.suggested_fix == "fix it"
        assert f.severity == "high"


class TestGetLineSnippet:
    """Tests for get_line_snippet."""

    def test_valid_line(self):
        lines = ["first", "second", "third"]
        assert get_line_snippet(lines, 1) == "first"
        assert get_line_snippet(lines, 2) == "second"
        assert get_line_snippet(lines, 3) == "third"

    def test_strips_whitespace(self):
        lines = ["  indented line  "]
        assert get_line_snippet(lines, 1) == "indented line"

    def test_line_out_of_range_high(self):
        lines = ["a", "b"]
        assert get_line_snippet(lines, 3) == ""
        assert get_line_snippet(lines, 99) == ""

    def test_line_out_of_range_low(self):
        lines = ["a", "b"]
        assert get_line_snippet(lines, 0) == ""

    def test_empty_lines(self):
        assert get_line_snippet([], 1) == ""
