import pytest

from crystal_ball.detector._utils import (
    Finding,
    get_line_snippet,
    has_blocking,
    BLOCKING_SEVERITIES,
    SEVERITY_ORDER,
)


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

    def test_is_blocking_high(self):
        f = Finding("x", "m", 1, "s", "f", severity="high")
        assert f.is_blocking is True

    def test_is_blocking_critical(self):
        f = Finding("x", "m", 1, "s", "f", severity="critical")
        assert f.is_blocking is True

    def test_is_not_blocking_medium(self):
        f = Finding("x", "m", 1, "s", "f", severity="medium")
        assert f.is_blocking is False

    def test_is_not_blocking_low(self):
        f = Finding("x", "m", 1, "s", "f", severity="low")
        assert f.is_blocking is False


class TestHasBlocking:
    """Tests for the has_blocking helper."""

    def test_empty_list(self):
        assert has_blocking([]) is False

    def test_only_medium(self):
        findings = [Finding("x", "m", 1, "s", "f", severity="medium")]
        assert has_blocking(findings) is False

    def test_mixed_with_high(self):
        findings = [
            Finding("x", "m", 1, "s", "f", severity="medium"),
            Finding("x", "m", 2, "s", "f", severity="high"),
        ]
        assert has_blocking(findings) is True


class TestSeverityConstants:
    """Validate severity ordering and blocking set."""

    def test_critical_is_highest(self):
        assert SEVERITY_ORDER["critical"] > SEVERITY_ORDER["high"]

    def test_blocking_includes_high_and_critical(self):
        assert "high" in BLOCKING_SEVERITIES
        assert "critical" in BLOCKING_SEVERITIES
        assert "medium" not in BLOCKING_SEVERITIES


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
