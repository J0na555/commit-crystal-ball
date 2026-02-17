import re

from crystal_ball.detector._utils import Finding

SECRET_PATTERNS = [
    (r'api_key\s*=\s*["\'][^"\']+["\']', "Remove and use env vars"),
    (r'password\s*=\s*["\'][^"\']+["\']', "Remove and use env vars"),
    (r'secret\s*=\s*["\'][^"\']+["\']', "Remove and use env vars"),
]


def check_hardcoded_secrets(lines: list[str], findings: list[Finding]) -> None:
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
