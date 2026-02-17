import ast
import re
from dataclasses import dataclass


@dataclass
class Finding:
    check_id: str
    message: str
    line: int
    snippet: str
    suggested_fix: str
    severity: str  # "high" | "medium" | "low"


def scan(content: str, filepath: str) -> list[Finding]:
    """Scan file content for potential issues. Returns list of findings."""
    
    findings: list[Finding] = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return findings

    lines = content.splitlines()

    # AST-based checks
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            _check_requests_timeout(node, lines, findings)
            _check_eval_usage(node, lines, findings)
            _check_sql_injection(node, lines, findings)
            _check_subprocess_shell(node, lines, findings)
            _check_yaml_load(node, lines, findings)
        if isinstance(node, ast.ExceptHandler):
            _check_bare_except(node, lines, findings)

    # Regex-based check for hardcoded secrets
    _check_hardcoded_secrets(lines, findings)

    return findings


def _get_line_snippet(lines: list[str], line_no: int) -> str:
    """Get a snippet for the given line number (1-based)."""
    if 0 <= line_no - 1 < len(lines):
        return lines[line_no - 1].strip()
    return ""


def _check_requests_timeout(node: ast.Call, lines: list[str], findings: list[Finding]) -> None:
    """Check for requests.get/post/put/delete without timeout."""

    if isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Name):
            if node.func.value.id == "requests" and node.func.attr in (
                "get",
                "post",
                "put",
                "delete",
            ):
                has_timeout = any(
                    kw.arg == "timeout" for kw in (node.keywords or [])
                )
                if not has_timeout:
                    line_no = node.lineno
                    findings.append(
                        Finding(
                            check_id="missing_timeout",
                            message=f"requests.{node.func.attr}() called without timeout - may hang indefinitely",
                            line=line_no,
                            snippet=_get_line_snippet(lines, line_no),
                            suggested_fix=f"requests.{node.func.attr}(..., timeout=5)",
                            severity="high",
                        )
                    )


def _check_bare_except(node: ast.ExceptHandler, lines: list[str], findings: list[Finding]) -> None:
    """Check for bare except: clauses without a type"""

    if node.type is None:
        line_no = node.lineno
        findings.append(
            Finding(
                check_id="bare_except",
                message="Bare except: catches all exceptions including KeyboardInterrupt",
                line=line_no,
                snippet=_get_line_snippet(lines, line_no),
                suggested_fix="except Exception:",
                severity="medium",
            )
        )


def _check_eval_usage(node: ast.Call, lines: list[str], findings: list[Finding]) -> None:
    """Detect dangerous eval/exec usage."""

    if isinstance(node.func, ast.Name):
        if node.func.id in ("eval", "exec", "compile"):
            findings.append(
                Finding(
                    check_id="eval_exec_usage",
                    message=f"{node.func.id}() executes or compiles arbitrary code - security risk",
                    line=node.lineno,
                    snippet=_get_line_snippet(lines, node.lineno),
                    suggested_fix="Use ast.literal_eval() for literals, or safer parsing",
                    severity="high",
                )
            )


def _is_unsafe_sql_arg(arg: ast.expr) -> bool:
    """Check if SQL argument uses string formatting (injection risk)."""

    if isinstance(arg, ast.BinOp):
        if isinstance(arg.op, ast.Mod):
            return True  # "SELECT %s" % var
        if isinstance(arg.op, ast.Add):
            return True  # "SELECT " + var
    if isinstance(arg, ast.JoinedStr):
        return True  # f"SELECT {var}"
    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute):
        if arg.func.attr == "format":
            return True  # "SELECT {}".format(var)
    return False


def _check_sql_injection(node: ast.Call, lines: list[str], findings: list[Finding]) -> None:
    """Detect raw SQL queries with string formatting."""

    if isinstance(node.func, ast.Attribute):
        if node.func.attr in ("execute", "executemany") and node.args:
            arg = node.args[0]
            if _is_unsafe_sql_arg(arg):
                findings.append(
                    Finding(
                        check_id="sql_injection",
                        message=f".{node.func.attr}() with string formatting - SQL injection risk",
                        line=node.lineno,
                        snippet=_get_line_snippet(lines, node.lineno),
                        suggested_fix="Use parameterized queries: cursor.execute(sql, (params,))",
                        severity="high",
                    )
                )


def _is_shell_true(node: ast.expr) -> bool:

    """Check if node represents True (shell=True)."""
    if isinstance(node, ast.Constant):
        return node.value is True
    if hasattr(ast, "NameConstant") and isinstance(node, ast.NameConstant):
        return node.value is True
    return False


def _check_subprocess_shell(node: ast.Call, lines: list[str], findings: list[Finding]) -> None:
    """Check for shell=True in subprocess calls."""

    if isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Name):
            if node.func.value.id == "subprocess":
                if node.func.attr in ("run", "call", "Popen", "check_output", "check_call"):
                    for kw in node.keywords or []:
                        if kw.arg == "shell" and _is_shell_true(kw.value):
                            findings.append(
                                Finding(
                                    check_id="subprocess_shell",
                                    message=f"subprocess.{node.func.attr}() with shell=True - command injection risk",
                                    line=node.lineno,
                                    snippet=_get_line_snippet(lines, node.lineno),
                                    suggested_fix="Use shell=False and pass args as list",
                                    severity="high",
                                )
                            )
                            break


def _get_loader_name(node: ast.expr) -> str:
    """Extract loader name from Loader=SafeLoader or Loader=yaml.SafeLoader."""

    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _check_yaml_load(node: ast.Call, lines: list[str], findings: list[Finding]) -> None:
    """Detect unsafe yaml.load() without Loader."""

    if isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Name):
            if node.func.attr == "load" and node.func.value.id == "yaml":
                has_safe_loader = any(
                    kw.arg == "Loader"
                    and _get_loader_name(kw.value) in ("SafeLoader", "FullLoader", "BaseLoader")
                    for kw in (node.keywords or [])
                )
                if not has_safe_loader:
                    findings.append(
                        Finding(
                            check_id="unsafe_yaml_load",
                            message="yaml.load() without Loader - arbitrary code execution risk",
                            line=node.lineno,
                            snippet=_get_line_snippet(lines, node.lineno),
                            suggested_fix="Use yaml.safe_load() or yaml.load(..., Loader=yaml.SafeLoader)",
                            severity="high",
                        )
                    )


SECRET_PATTERNS = [
    (r'api_key\s*=\s*["\'][^"\']+["\']', "Remove and use env vars"),
    (r'password\s*=\s*["\'][^"\']+["\']', "Remove and use env vars"),
    (r'secret\s*=\s*["\'][^"\']+["\']', "Remove and use env vars"),
]


def _check_hardcoded_secrets(lines: list[str], findings: list[Finding]) -> None:
    """Check for hardcoded api keys, passwords and secrets via regex."""

    for i, line in enumerate(lines):
        for pattern, fix in SECRET_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append(
                    Finding(
                        check_id="hardcoded_secrets",
                        message="Potential hardcoded secret detected",
                        line=i + 1,
                        snippet=line.strip(),
                        suggested_fix=fix,
                        severity="high",
                    )
                )
                break
