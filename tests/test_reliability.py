import ast

import pytest

from crystal_ball.detector.reliability import check_bare_except, check_requests_timeout


def _parse_and_get_call(code: str) -> ast.Call:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            return node
    raise ValueError("No Call node found")


def _parse_and_get_except_handler(code: str) -> ast.ExceptHandler:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            return node
    raise ValueError("No ExceptHandler found")


class TestCheckRequestsTimeout:
    """Tests for check_requests_timeout."""

    def test_requests_get_without_timeout_detected(self):
        code = "requests.get(url)"
        node = _parse_and_get_call(code)
        findings = []
        check_requests_timeout(node, code.splitlines(), findings)
        assert len(findings) == 1
        assert findings[0].check_id == "missing_timeout"

    def test_requests_post_without_timeout_detected(self):
        code = "requests.post(url)"
        node = _parse_and_get_call(code)
        findings = []
        check_requests_timeout(node, code.splitlines(), findings)
        assert len(findings) == 1

    def test_requests_put_without_timeout_detected(self):
        code = "requests.put(url)"
        node = _parse_and_get_call(code)
        findings = []
        check_requests_timeout(node, code.splitlines(), findings)
        assert len(findings) == 1

    def test_requests_delete_without_timeout_detected(self):
        code = "requests.delete(url)"
        node = _parse_and_get_call(code)
        findings = []
        check_requests_timeout(node, code.splitlines(), findings)
        assert len(findings) == 1

    def test_requests_get_with_timeout_not_detected(self):
        code = "requests.get(url, timeout=5)"
        node = _parse_and_get_call(code)
        findings = []
        check_requests_timeout(node, code.splitlines(), findings)
        assert len(findings) == 0

    def test_requests_get_with_timeout_kwarg_not_detected(self):
        code = "requests.get(url, timeout=10)"
        node = _parse_and_get_call(code)
        findings = []
        check_requests_timeout(node, code.splitlines(), findings)
        assert len(findings) == 0

    def test_other_module_not_detected(self):
        code = "other.get(url)"
        node = _parse_and_get_call(code)
        findings = []
        check_requests_timeout(node, code.splitlines(), findings)
        assert len(findings) == 0

    def test_requests_head_not_checked(self):
        # head is not in the list - only get, post, put, delete
        code = "requests.head(url)"
        node = _parse_and_get_call(code)
        findings = []
        check_requests_timeout(node, code.splitlines(), findings)
        assert len(findings) == 0


class TestCheckBareExcept:
    """Tests for check_bare_except."""

    def test_bare_except_detected(self):
        code = """
try:
    x = 1
except:
    pass
"""
        node = _parse_and_get_except_handler(code)
        findings = []
        check_bare_except(node, code.splitlines(), findings)
        assert len(findings) == 1
        assert findings[0].check_id == "bare_except"

    def test_except_exception_not_detected(self):
        code = """
try:
    x = 1
except Exception:
    pass
"""
        node = _parse_and_get_except_handler(code)
        findings = []
        check_bare_except(node, code.splitlines(), findings)
        assert len(findings) == 0

    def test_except_value_error_not_detected(self):
        code = """
try:
    x = 1
except ValueError:
    pass
"""
        node = _parse_and_get_except_handler(code)
        findings = []
        check_bare_except(node, code.splitlines(), findings)
        assert len(findings) == 0
