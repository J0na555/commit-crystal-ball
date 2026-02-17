import ast

from crystal_ball.detector._utils import Finding, get_line_snippet


def check_requests_timeout(node: ast.Call, lines: list[str], findings: list[Finding]) -> None:
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
                            snippet=get_line_snippet(lines, line_no),
                            suggested_fix=f"requests.{node.func.attr}(..., timeout=5)",
                            severity="high",
                        )
                    )


def check_bare_except(node: ast.ExceptHandler, lines: list[str], findings: list[Finding]) -> None:
    """Check for bare except: clauses without a type."""
    if node.type is None:
        line_no = node.lineno
        findings.append(
            Finding(
                check_id="bare_except",
                message="Bare except: catches all exceptions including KeyboardInterrupt",
                line=line_no,
                snippet=get_line_snippet(lines, line_no),
                suggested_fix="except Exception:",
                severity="medium",
            )
        )
