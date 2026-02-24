import io
from unittest.mock import MagicMock

import pytest

from crystal_ball.detector import Finding
from crystal_ball.narrator import ALL_TONES
from crystal_ball.reporter import print_findings


class TestPrintFindings:
    """Tests for print_findings."""

    def test_empty_findings_does_not_print(self):
        """Should not call console.print when no findings."""
        with pytest.MonkeyPatch.context() as m:
            mock_console = MagicMock()
            m.setattr("crystal_ball.reporter.console", mock_console)
            print_findings([], "test.py")
            mock_console.print.assert_not_called()

    def test_findings_prints_panels(self):
        """Should print a panel for each finding."""
        findings = [
            Finding(
                check_id="eval_exec_usage",
                message="Test message",
                line=1,
                snippet="eval('x')",
                suggested_fix="Fix it",
                severity="high",
            )
        ]
        with pytest.MonkeyPatch.context() as m:
            mock_console = MagicMock()
            m.setattr("crystal_ball.reporter.console", mock_console)
            print_findings(findings, "test.py")
            assert mock_console.print.call_count >= 2  # Panel + newline

    def test_severity_styles(self):
        """High severity findings should use red style."""
        findings = [
            Finding(
                check_id="eval_exec_usage",
                message="High",
                line=1,
                snippet="eval('x')",
                suggested_fix="fix",
                severity="high",
            ),
            Finding(
                check_id="bare_except",
                message="Medium",
                line=2,
                snippet="except:",
                suggested_fix="fix",
                severity="medium",
            ),
        ]
        with pytest.MonkeyPatch.context() as m:
            mock_console = MagicMock()
            m.setattr("crystal_ball.reporter.console", mock_console)
            print_findings(findings, "test.py")
            mock_console.print.assert_called()

    def test_narrative_included_in_output(self):
        """Narrator-generated risk summary should appear in output."""
        findings = [
            Finding(
                check_id="eval_exec_usage",
                message="eval() executes arbitrary code",
                line=1,
                snippet="eval('x')",
                suggested_fix="Use ast.literal_eval()",
                severity="high",
            )
        ]
        buf = io.StringIO()
        with pytest.MonkeyPatch.context() as m:
            from rich.console import Console

            real_console = Console(file=buf, force_terminal=True, width=120)
            m.setattr("crystal_ball.reporter.console", real_console)
            print_findings(findings, "test.py", tone="oracle")
        output = buf.getvalue()
        assert "Risk" in output
        assert "eval_exec_usage" in output

    @pytest.mark.parametrize("tone", ALL_TONES)
    def test_all_tones_render_without_error(self, tone):
        findings = [
            Finding(
                check_id="sql_injection",
                message="SQL injection risk",
                line=5,
                snippet="cursor.execute(f'SELECT {x}')",
                suggested_fix="Use parameterized queries",
                severity="high",
            )
        ]
        buf = io.StringIO()
        with pytest.MonkeyPatch.context() as m:
            from rich.console import Console

            real_console = Console(file=buf, force_terminal=True, width=120)
            m.setattr("crystal_ball.reporter.console", real_console)
            print_findings(findings, "test.py", tone=tone)
        output = buf.getvalue()
        assert "sql_injection" in output
        assert "Suggested Fix" in output

    def test_suggested_fix_always_visible(self):
        """suggested_fix must always appear in output regardless of tone."""
        findings = [
            Finding(
                check_id="subprocess_shell",
                message="shell=True risk",
                line=3,
                snippet="subprocess.run(cmd, shell=True)",
                suggested_fix="Use shell=False and pass args as list",
                severity="high",
            )
        ]
        for tone in ALL_TONES:
            buf = io.StringIO()
            with pytest.MonkeyPatch.context() as m:
                from rich.console import Console

                real_console = Console(file=buf, force_terminal=True, width=120)
                m.setattr("crystal_ball.reporter.console", real_console)
                print_findings(findings, "test.py", tone=tone)
            assert "shell=False" in buf.getvalue()
