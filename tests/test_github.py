"""Tests for crystal_ball.github annotation output."""

import io

from crystal_ball.detector import Finding
from crystal_ball.github import format_annotation, print_github_annotations


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


class TestFormatAnnotation:
    """GitHub Actions annotation line formatting."""

    def test_high_severity_is_error(self):
        line = format_annotation(_make_finding(severity="high"), "app.py")
        assert line.startswith("::error ")

    def test_critical_severity_is_error(self):
        line = format_annotation(_make_finding(severity="critical"), "app.py")
        assert line.startswith("::error ")

    def test_medium_severity_is_warning(self):
        line = format_annotation(_make_finding(severity="medium"), "app.py")
        assert line.startswith("::warning ")

    def test_low_severity_is_notice(self):
        line = format_annotation(_make_finding(severity="low"), "app.py")
        assert line.startswith("::notice ")

    def test_includes_file_and_line(self):
        line = format_annotation(_make_finding(line=42), "src/app.py")
        assert "file=src/app.py" in line
        assert "line=42" in line

    def test_includes_message_and_fix(self):
        f = _make_finding(message="danger", suggested_fix="use safe thing")
        line = format_annotation(f, "app.py")
        assert "danger" in line
        assert "use safe thing" in line

    def test_includes_check_id_in_title(self):
        line = format_annotation(_make_finding(), "app.py")
        assert "eval_exec_usage" in line


class TestPrintGithubAnnotations:
    """Integration test for writing annotations to a stream."""

    def test_prints_one_line_per_finding(self):
        findings = [_make_finding(line=1), _make_finding(line=2)]
        buf = io.StringIO()
        print_github_annotations(findings, "app.py", stream=buf)
        lines = buf.getvalue().strip().splitlines()
        assert len(lines) == 2

    def test_empty_findings_produces_no_output(self):
        buf = io.StringIO()
        print_github_annotations([], "app.py", stream=buf)
        assert buf.getvalue() == ""
