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
