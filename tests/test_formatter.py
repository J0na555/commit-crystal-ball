"""Tests for crystal_ball.formatter ANSI output."""

import io

import pytest

from crystal_ball.detector import Finding
from crystal_ball.formatter import format_findings, _Ansi, _supports_colour


def _make_finding(**overrides) -> Finding:
    defaults = dict(
        check_id="eval_exec_usage",
        message="eval() executes arbitrary code",
        line=10,
        snippet="eval(user_input)",
        suggested_fix="Use ast.literal_eval()",
        severity="high",
    )
    defaults.update(overrides)
    return Finding(**defaults)


class TestAnsiHelper:
    """Low-level ANSI escape-code helper."""

    def test_style_with_colour_enabled(self):
        ansi = _Ansi(colour=True)
        styled = ansi.style("hello", _Ansi.RED)
        assert "\033[31m" in styled
        assert "hello" in styled

    def test_style_with_colour_disabled(self):
        ansi = _Ansi(colour=False)
        styled = ansi.style("hello", _Ansi.RED)
        assert styled == "hello"


class TestFormatFindings:
    """Integration tests for the full formatter."""

    def test_empty_findings_produces_no_output(self):
        buf = io.StringIO()
        format_findings([], "test.py", stream=buf)
        assert buf.getvalue() == ""

    def test_findings_include_check_id(self):
        buf = io.StringIO()
        format_findings([_make_finding()], "test.py", stream=buf, colour=False)
        assert "eval_exec_usage" in buf.getvalue()

    def test_findings_include_severity_label(self):
        buf = io.StringIO()
        format_findings([_make_finding(severity="high")], "test.py", stream=buf, colour=False)
        assert "HIGH" in buf.getvalue()

    def test_findings_include_suggested_fix(self):
        buf = io.StringIO()
        format_findings([_make_finding()], "test.py", stream=buf, colour=False)
        assert "ast.literal_eval()" in buf.getvalue()

    def test_summary_line_shows_blocking_count(self):
        buf = io.StringIO()
        findings = [_make_finding(severity="high"), _make_finding(severity="medium", line=20)]
        format_findings(findings, "test.py", stream=buf, colour=False)
        output = buf.getvalue()
        assert "2 finding(s)" in output
        assert "1 blocking" in output

    def test_critical_severity_shown(self):
        buf = io.StringIO()
        format_findings([_make_finding(severity="critical")], "test.py", stream=buf, colour=False)
        assert "CRITICAL" in buf.getvalue()

    @pytest.mark.parametrize("tone", ["oracle", "dramatic", "minimalist", "professional"])
    def test_all_tones_render(self, tone):
        buf = io.StringIO()
        format_findings([_make_finding()], "test.py", tone=tone, stream=buf, colour=False)
        assert len(buf.getvalue()) > 0
