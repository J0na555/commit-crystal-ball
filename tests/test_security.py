import ast

import pytest

from crystal_ball.detector.security import (
    check_eval_usage,
    check_sql_injection,
    check_subprocess_shell,
    check_yaml_load,
)


def _parse_and_get_call(code: str) -> ast.Call:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            return node
    raise ValueError("No Call node found")


def _parse_and_get_calls(code: str) -> list[ast.Call]:
    tree = ast.parse(code)
    return [n for n in ast.walk(tree) if isinstance(n, ast.Call)]


class TestCheckEvalUsage:
    """Tests for check_eval_usage."""

    def test_eval_detected(self):
        code = "eval('1+1')"
        node = _parse_and_get_call(code)
        findings = []
        check_eval_usage(node, code.splitlines(), findings)
        assert len(findings) == 1
        assert findings[0].check_id == "eval_exec_usage"
        assert "eval" in findings[0].message

    def test_exec_detected(self):
        code = "exec('print(1)')"
        node = _parse_and_get_call(code)
        findings = []
        check_eval_usage(node, code.splitlines(), findings)
        assert len(findings) == 1
        assert "exec" in findings[0].message

    def test_compile_detected(self):
        code = "compile('x', '<string>', 'exec')"
        node = _parse_and_get_call(code)
        findings = []
        check_eval_usage(node, code.splitlines(), findings)
        assert len(findings) == 1
        assert "compile" in findings[0].message

    def test_safe_call_not_detected(self):
        code = "print('hello')"
        node = _parse_and_get_call(code)
        findings = []
        check_eval_usage(node, code.splitlines(), findings)
        assert len(findings) == 0


class TestCheckSqlInjection:
    """Tests for check_sql_injection."""

    def test_execute_with_mod_format_detected(self):
        code = "cursor.execute('SELECT %s' % var)"
        node = _parse_and_get_call(code)
        findings = []
        check_sql_injection(node, code.splitlines(), findings)
        assert len(findings) == 1
        assert findings[0].check_id == "sql_injection"

    def test_execute_with_add_detected(self):
        code = 'cursor.execute("SELECT " + var)'
        node = _parse_and_get_call(code)
        findings = []
        check_sql_injection(node, code.splitlines(), findings)
        assert len(findings) == 1

    def test_execute_with_fstring_detected(self):
        code = 'cursor.execute(f"SELECT {col}")'
        node = _parse_and_get_call(code)
        findings = []
        check_sql_injection(node, code.splitlines(), findings)
        assert len(findings) == 1

    def test_execute_with_format_method_detected(self):
        code = 'cursor.execute("SELECT {}".format(var))'
        node = _parse_and_get_call(code)
        findings = []
        check_sql_injection(node, code.splitlines(), findings)
        assert len(findings) == 1

    def test_executemany_unsafe_detected(self):
        code = "cursor.executemany('INSERT %s' % table, rows)"
        node = _parse_and_get_call(code)
        findings = []
        check_sql_injection(node, code.splitlines(), findings)
        assert len(findings) == 1

    def test_execute_safe_not_detected(self):
        code = "cursor.execute('SELECT 1', ())"
        node = _parse_and_get_call(code)
        findings = []
        check_sql_injection(node, code.splitlines(), findings)
        assert len(findings) == 0


class TestCheckSubprocessShell:
    """Tests for check_subprocess_shell."""

    def test_subprocess_run_shell_true_detected(self):
        code = "subprocess.run('ls', shell=True)"
        node = _parse_and_get_call(code)
        findings = []
        check_subprocess_shell(node, code.splitlines(), findings)
        assert len(findings) == 1
        assert findings[0].check_id == "subprocess_shell"

    def test_subprocess_call_shell_true_detected(self):
        code = "subprocess.call('ls', shell=True)"
        node = _parse_and_get_call(code)
        findings = []
        check_subprocess_shell(node, code.splitlines(), findings)
        assert len(findings) == 1

    def test_subprocess_popen_shell_true_detected(self):
        code = "subprocess.Popen('ls', shell=True)"
        node = _parse_and_get_call(code)
        findings = []
        check_subprocess_shell(node, code.splitlines(), findings)
        assert len(findings) == 1

    def test_subprocess_check_output_shell_true_detected(self):
        code = "subprocess.check_output('ls', shell=True)"
        node = _parse_and_get_call(code)
        findings = []
        check_subprocess_shell(node, code.splitlines(), findings)
        assert len(findings) == 1

    def test_subprocess_check_call_shell_true_detected(self):
        code = "subprocess.check_call('ls', shell=True)"
        node = _parse_and_get_call(code)
        findings = []
        check_subprocess_shell(node, code.splitlines(), findings)
        assert len(findings) == 1

    def test_subprocess_run_shell_false_not_detected(self):
        code = "subprocess.run(['ls'], shell=False)"
        node = _parse_and_get_call(code)
        findings = []
        check_subprocess_shell(node, code.splitlines(), findings)
        assert len(findings) == 0

    def test_subprocess_run_no_shell_not_detected(self):
        code = "subprocess.run(['ls'])"
        node = _parse_and_get_call(code)
        findings = []
        check_subprocess_shell(node, code.splitlines(), findings)
        assert len(findings) == 0


class TestCheckYamlLoad:
    """Tests for check_yaml_load."""

    def test_yaml_load_without_loader_detected(self):
        code = "yaml.load(data)"
        node = _parse_and_get_call(code)
        findings = []
        check_yaml_load(node, code.splitlines(), findings)
        assert len(findings) == 1
        assert findings[0].check_id == "unsafe_yaml_load"

    def test_yaml_load_with_safe_loader_not_detected(self):
        code = "yaml.load(data, Loader=yaml.SafeLoader)"
        node = _parse_and_get_call(code)
        findings = []
        check_yaml_load(node, code.splitlines(), findings)
        assert len(findings) == 0

    def test_yaml_load_with_full_loader_not_detected(self):
        code = "yaml.load(data, Loader=yaml.FullLoader)"
        node = _parse_and_get_call(code)
        findings = []
        check_yaml_load(node, code.splitlines(), findings)
        assert len(findings) == 0

    def test_yaml_load_with_base_loader_not_detected(self):
        code = "yaml.load(data, Loader=yaml.BaseLoader)"
        node = _parse_and_get_call(code)
        findings = []
        check_yaml_load(node, code.splitlines(), findings)
        assert len(findings) == 0

    def test_yaml_safe_load_not_detected(self):
        code = "yaml.safe_load(data)"
        node = _parse_and_get_call(code)
        findings = []
        check_yaml_load(node, code.splitlines(), findings)
        assert len(findings) == 0
