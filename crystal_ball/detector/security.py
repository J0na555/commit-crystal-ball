import ast

from crystal_ball.detector._utils import Finding, get_line_snippet


def check_eval_usage(node: ast.Call, lines: list[str], findings: list[Finding]) -> None:
    """Detect dangerous eval/exec usage."""
    if isinstance(node.func, ast.Name):
        if node.func.id in ("eval", "exec", "compile"):
            findings.append(
                Finding(
                    check_id="eval_exec_usage",
                    message=f"{node.func.id}() executes or compiles arbitrary code - security risk",
                    line=node.lineno,
                    snippet=get_line_snippet(lines, node.lineno),
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


def check_sql_injection(node: ast.Call, lines: list[str], findings: list[Finding]) -> None:
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
                        snippet=get_line_snippet(lines, node.lineno),
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


def check_subprocess_shell(node: ast.Call, lines: list[str], findings: list[Finding]) -> None:
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
                                    snippet=get_line_snippet(lines, node.lineno),
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


def check_yaml_load(node: ast.Call, lines: list[str], findings: list[Finding]) -> None:
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
                            snippet=get_line_snippet(lines, node.lineno),
                            suggested_fix="Use yaml.safe_load() or yaml.load(..., Loader=yaml.SafeLoader)",
                            severity="high",
                        )
                    )
