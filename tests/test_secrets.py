import pytest

from crystal_ball.detector.secrets import check_hardcoded_secrets


class TestCheckHardcodedSecrets:
    """Tests for check_hardcoded_secrets."""

    def test_api_key_detected(self):
        lines = ["api_key = 'sk-12345'"]
        findings = []
        check_hardcoded_secrets(lines, findings)
        assert len(findings) == 1
        assert findings[0].check_id == "hardcoded_secrets"
        assert "api_key" in findings[0].snippet

    def test_api_key_double_quotes_detected(self):
        lines = ['api_key = "sk-12345"']
        findings = []
        check_hardcoded_secrets(lines, findings)
        assert len(findings) == 1

    def test_password_detected(self):
        lines = ["password = 'secret123'"]
        findings = []
        check_hardcoded_secrets(lines, findings)
        assert len(findings) == 1

    def test_secret_detected(self):
        lines = ["secret = 'my-secret'"]
        findings = []
        check_hardcoded_secrets(lines, findings)
        assert len(findings) == 1

    def test_case_insensitive_api_key(self):
        lines = ["API_KEY = 'sk-12345'"]
        findings = []
        check_hardcoded_secrets(lines, findings)
        assert len(findings) == 1

    def test_no_secret_not_detected(self):
        lines = ["x = 42", "name = 'hello'"]
        findings = []
        check_hardcoded_secrets(lines, findings)
        assert len(findings) == 0

    def test_empty_lines_not_detected(self):
        lines = []
        findings = []
        check_hardcoded_secrets(lines, findings)
        assert len(findings) == 0

    def test_multiple_secrets_multiple_findings(self):
        lines = [
            "api_key = 'key1'",
            "password = 'pass1'",
        ]
        findings = []
        check_hardcoded_secrets(lines, findings)
        assert len(findings) == 2
