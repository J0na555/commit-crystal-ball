import pytest

from crystal_ball.detector import Finding, scan


class TestScan:
    """Tests for the main scan function."""

    def test_empty_file_no_findings(self):
        findings = scan("", "test.py")
        assert findings == []

    def test_syntax_error_returns_empty(self):
        findings = scan("def broken(  ", "test.py")
        assert findings == []

    def test_clean_code_no_findings(self):
        code = """
def main():
    x = 1 + 1
    return x
"""
        findings = scan(code, "test.py")
        assert len(findings) == 0

    def test_sample_file_findings(self):
        """Test against sample.py - has requests without timeout and bare except."""
        code = '''
"""Sample file for testing crystal-ball scan."""

import requests

url = "https://example.com"
response = requests.get(url)

try:
    x = 1 / 0
except:
    pass
'''
        findings = scan(code, "sample.py")
        check_ids = [f.check_id for f in findings]
        assert "missing_timeout" in check_ids
        assert "bare_except" in check_ids

    def test_eval_detected_in_scan(self):
        code = "result = eval('1+1')"
        findings = scan(code, "test.py")
        assert any(f.check_id == "eval_exec_usage" for f in findings)

    def test_sql_injection_detected_in_scan(self):
        code = "cursor.execute('SELECT %s' % var)"
        findings = scan(code, "test.py")
        assert any(f.check_id == "sql_injection" for f in findings)

    def test_subprocess_shell_detected_in_scan(self):
        code = "subprocess.run('ls', shell=True)"
        findings = scan(code, "test.py")
        assert any(f.check_id == "subprocess_shell" for f in findings)

    def test_yaml_load_detected_in_scan(self):
        code = "data = yaml.load(f)"
        findings = scan(code, "test.py")
        assert any(f.check_id == "unsafe_yaml_load" for f in findings)

    def test_hardcoded_secret_detected_in_scan(self):
        code = "api_key = 'sk-12345'"
        findings = scan(code, "test.py")
        assert any(f.check_id == "hardcoded_secrets" for f in findings)

    def test_findings_have_required_fields(self):
        code = "eval('1')"
        findings = scan(code, "test.py")
        assert len(findings) >= 1
        f = findings[0]
        assert hasattr(f, "check_id")
        assert hasattr(f, "message")
        assert hasattr(f, "line")
        assert hasattr(f, "snippet")
        assert hasattr(f, "suggested_fix")
        assert hasattr(f, "severity")

    def test_filepath_passed_through(self):
        """Filepath is passed to scan but not used in findings - verify scan accepts it."""
        findings = scan("x = 1", "any/path/file.py")
        assert findings == []
