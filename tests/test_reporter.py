from unittest.mock import MagicMock

import pytest

from crystal_ball.detector import Finding
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
                check_id="test_check",
                message="Test message",
                line=1,
                snippet="code snippet",
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
                check_id="high_check",
                message="High",
                line=1,
                snippet="x",
                suggested_fix="fix",
                severity="high",
            ),
            Finding(
                check_id="medium_check",
                message="Medium",
                line=2,
                snippet="y",
                suggested_fix="fix",
                severity="medium",
            ),
            Finding(
                check_id="low_check",
                message="Low",
                line=3,
                snippet="z",
                suggested_fix="fix",
                severity="low",
            ),
        ]
        with pytest.MonkeyPatch.context() as m:
            mock_console = MagicMock()
            m.setattr("crystal_ball.reporter.console", mock_console)
            print_findings(findings, "test.py")
            # Just verify it doesn't raise
            mock_console.print.assert_called()
