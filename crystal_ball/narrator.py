from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal

from crystal_ball.detector._utils import Finding

ToneMode = Literal["oracle", "dramatic", "minimalist", "professional"]

DEFAULT_TONE: ToneMode = "oracle"
ALL_TONES: tuple[ToneMode, ...] = ("oracle", "dramatic", "minimalist", "professional")


@dataclass(frozen=True)
class Narrative:
    """Formatted narrative output for a single finding."""

    headline: str
    risk_summary: str


@dataclass(frozen=True)
class _CheckTemplate:
    """Per-tone headline and risk variants for a single check_id."""

    headlines: tuple[str, ...]
    risks: tuple[str, ...]


# ---------------------------------------------------------------------------
# Template registry — one entry per check_id, one sub-entry per tone
# ---------------------------------------------------------------------------

_TEMPLATES: dict[str, dict[ToneMode, _CheckTemplate]] = {
    "eval_exec_usage": {
        "oracle": _CheckTemplate(
            headlines=(
                "The Crystal Ball trembles \u2014 arbitrary code will execute",
                "A rift in reality: untrusted code runs unchecked",
            ),
            risks=(
                "An attacker slips a payload into the call on line {line} and owns the process.",
                "The eval becomes the front door \u2014 no lock, no bouncer, just open execution.",
            ),
        ),
        "dramatic": _CheckTemplate(
            headlines=(
                "SOMETHING UNINVITED WILL EXECUTE",
                "THE CALL IS COMING FROM INSIDE THE EVAL",
            ),
            risks=(
                "At 3 AM, the server starts running code nobody wrote. The trail leads to line {line}.",
                "The payload arrives disguised as user input. By morning, it has spawned a reverse shell.",
            ),
        ),
        "minimalist": _CheckTemplate(
            headlines=("Arbitrary code execution via eval/exec",),
            risks=("Untrusted input passed to eval/exec on line {line} allows arbitrary code execution.",),
        ),
        "professional": _CheckTemplate(
            headlines=("Code Execution Risk \u2014 eval/exec with potentially untrusted input",),
            risks=("Use of eval/exec on line {line} permits arbitrary code execution if input is attacker-controlled.",),
        ),
    },
    "sql_injection": {
        "oracle": _CheckTemplate(
            headlines=(
                "The database whispers its secrets to strangers",
                "A vision of data spilling through unguarded queries",
            ),
            risks=(
                "An unsanitized query on line {line} becomes the key to every row in the table.",
                "The Crystal Ball sees DROP TABLE in your future \u2014 the query string is the open gate.",
            ),
        ),
        "dramatic": _CheckTemplate(
            headlines=(
                "YOUR DATABASE IS AN OPEN BOOK",
                "THEY ARE READING YOUR DATA RIGHT NOW",
            ),
            risks=(
                "The attacker types a single apostrophe and the entire users table spills onto the screen.",
                "One malformed input. One missing parameterization. The whole database, exfiltrated overnight.",
            ),
        ),
        "minimalist": _CheckTemplate(
            headlines=("SQL injection via string formatting",),
            risks=("String formatting in SQL query on line {line} allows injection of arbitrary SQL.",),
        ),
        "professional": _CheckTemplate(
            headlines=("SQL Injection Risk \u2014 unparameterized query",),
            risks=("Query construction via string formatting on line {line} is vulnerable to SQL injection attacks.",),
        ),
    },
    "subprocess_shell": {
        "oracle": _CheckTemplate(
            headlines=(
                "The shell opens \u2014 and it answers to anyone who asks",
                "A dark portal: shell=True invites the unknown",
            ),
            risks=(
                "With shell=True, an attacker's input becomes a system command on line {line}.",
                "The subprocess call trusts the shell blindly \u2014 command injection is one semicolon away.",
            ),
        ),
        "dramatic": _CheckTemplate(
            headlines=(
                "THE SHELL DOES NOT DISCRIMINATE",
                "SOMEONE ELSE IS TYPING COMMANDS",
            ),
            risks=(
                "The attacker appends '; rm -rf /' and the server obeys without question.",
                "shell=True on line {line} \u2014 every user input becomes root's next command.",
            ),
        ),
        "minimalist": _CheckTemplate(
            headlines=("Command injection via shell=True",),
            risks=("subprocess call with shell=True on line {line} permits command injection.",),
        ),
        "professional": _CheckTemplate(
            headlines=("Command Injection Risk \u2014 subprocess with shell=True",),
            risks=("The subprocess invocation on line {line} uses shell=True, creating a command injection vector.",),
        ),
    },
    "unsafe_yaml_load": {
        "oracle": _CheckTemplate(
            headlines=(
                "The YAML file hides a serpent within",
                "A configuration file becomes an execution vector",
            ),
            risks=(
                "yaml.load() without SafeLoader deserializes arbitrary Python objects \u2014 remote code execution awaits.",
                "The Crystal Ball sees a poisoned config file. One load() call, and the attacker's code runs.",
            ),
        ),
        "dramatic": _CheckTemplate(
            headlines=(
                "THE CONFIG FILE IS ALIVE",
                "THE DESERIALIZATION NIGHTMARE BEGINS",
            ),
            risks=(
                "Someone slips a crafted YAML into the pipeline. yaml.load() executes their payload on line {line}.",
                "The config looks normal. Inside, a Python object waits to execute.",
            ),
        ),
        "minimalist": _CheckTemplate(
            headlines=("Unsafe YAML deserialization",),
            risks=("yaml.load() without Loader on line {line} allows arbitrary code execution via crafted YAML.",),
        ),
        "professional": _CheckTemplate(
            headlines=("Deserialization Risk \u2014 yaml.load() without safe Loader",),
            risks=("The yaml.load() call on line {line} lacks a safe Loader, enabling arbitrary object instantiation.",),
        ),
    },
    "hardcoded_secrets": {
        "oracle": _CheckTemplate(
            headlines=(
                "A secret lies bare for all to see",
                "The Crystal Ball sees your keys \u2014 and so will the world",
            ),
            risks=(
                "Hardcoded credentials on line {line} will end up in version control, then in the wrong hands.",
                "The secret sits in plain text. One git push, and it lives in every clone forever.",
            ),
        ),
        "dramatic": _CheckTemplate(
            headlines=(
                "YOUR SECRETS ARE NOT SECRET",
                "THE API KEY IS CALLING FROM INSIDE THE REPO",
            ),
            risks=(
                "The credential on line {line} is already in the git history. Rotating it won't erase the past.",
                "Bots scan every public push. Your hardcoded key will be found in under 30 seconds.",
            ),
        ),
        "minimalist": _CheckTemplate(
            headlines=("Hardcoded credential detected",),
            risks=("Potential secret on line {line} should be moved to environment variables.",),
        ),
        "professional": _CheckTemplate(
            headlines=("Credential Exposure \u2014 hardcoded secret in source",),
            risks=("A hardcoded credential on line {line} risks exposure via version control or build artifacts.",),
        ),
    },
    "missing_timeout": {
        "oracle": _CheckTemplate(
            headlines=(
                "The request departs \u2014 it may never return",
                "A thread vanishes into the void, waiting forever",
            ),
            risks=(
                "Without a timeout, the request on line {line} hangs indefinitely when the remote server goes silent.",
                "The Crystal Ball sees a thread pool drained dry \u2014 all workers stuck waiting on a dead endpoint.",
            ),
        ),
        "dramatic": _CheckTemplate(
            headlines=(
                "THE REQUEST THAT NEVER CAME BACK",
                "HUNG THREADS PILE UP IN THE DARKNESS",
            ),
            risks=(
                "One by one, the worker threads send requests and never return. The server grinds to a halt.",
                "The remote endpoint dies. Your service follows, one hung connection at a time.",
            ),
        ),
        "minimalist": _CheckTemplate(
            headlines=("HTTP request without timeout",),
            risks=("requests call on line {line} has no timeout and may hang indefinitely.",),
        ),
        "professional": _CheckTemplate(
            headlines=("Reliability Risk \u2014 HTTP request missing timeout",),
            risks=("The HTTP request on line {line} lacks a timeout parameter, risking indefinite blocking.",),
        ),
    },
    "bare_except": {
        "oracle": _CheckTemplate(
            headlines=(
                "The except clause catches everything \u2014 even what it shouldn't",
                "A net so wide it traps the wind itself",
            ),
            risks=(
                "Bare except on line {line} swallows KeyboardInterrupt, SystemExit, and real bugs alike.",
                "Errors vanish silently into the bare except. Debugging becomes archaeology.",
            ),
        ),
        "dramatic": _CheckTemplate(
            headlines=(
                "ERRORS GO IN. NOTHING COMES OUT.",
                "THE SILENT SWALLOWER LURKS ON LINE {line}",
            ),
            risks=(
                "KeyboardInterrupt? Caught. SystemExit? Caught. The actual bug? Buried alive.",
                "The bare except devours every traceback. When things go wrong, you will never know why.",
            ),
        ),
        "minimalist": _CheckTemplate(
            headlines=("Bare except clause",),
            risks=("Bare except on line {line} catches all exceptions including KeyboardInterrupt.",),
        ),
        "professional": _CheckTemplate(
            headlines=("Exception Handling Risk \u2014 bare except clause",),
            risks=("The bare except on line {line} catches all BaseException subclasses, masking critical errors.",),
        ),
    },
}

# ---------------------------------------------------------------------------
# Fallback templates for unknown check_ids
# ---------------------------------------------------------------------------

_DEFAULT_TEMPLATES: dict[ToneMode, _CheckTemplate] = {
    "oracle": _CheckTemplate(
        headlines=("The Crystal Ball detects a disturbance on line {line}",),
        risks=("{message}",),
    ),
    "dramatic": _CheckTemplate(
        headlines=("SOMETHING IS WRONG ON LINE {line}",),
        risks=("{message}",),
    ),
    "minimalist": _CheckTemplate(
        headlines=("Issue detected: {check_id}",),
        risks=("{message}",),
    ),
    "professional": _CheckTemplate(
        headlines=("Finding: {check_id}",),
        risks=("{message}",),
    ),
}


def _stable_index(finding: Finding) -> int:
    """Derive a deterministic variant index from the finding itself.

    Uses MD5 of (check_id, line) so different findings naturally pick
    different variants while the same finding always gets the same one.
    """
    raw = f"{finding.check_id}:{finding.line}".encode()
    return int(hashlib.md5(raw).hexdigest(), 16)


def format_narrative(
    finding: Finding,
    tone: ToneMode = DEFAULT_TONE,
    *,
    seed: int | None = None,
) -> Narrative:
    """Produce a deterministic narrative for a finding.

    Parameters
    ----------
    finding:
        Structured finding from a detector.
    tone:
        One of ``"oracle"``, ``"dramatic"``, ``"minimalist"``, ``"professional"``.
    seed:
        Explicit variant selector.  When *None* (default), a stable hash of
        the finding is used so different findings get different variants but
        the same finding always produces the same output.
    """
    check_templates = _TEMPLATES.get(finding.check_id, {})
    template = check_templates.get(tone) or _DEFAULT_TEMPLATES[tone]

    idx = _stable_index(finding) if seed is None else seed

    headline = template.headlines[idx % len(template.headlines)]
    risk = template.risks[idx % len(template.risks)]

    fmt_vars = {
        "check_id": finding.check_id,
        "message": finding.message,
        "line": finding.line,
        "snippet": finding.snippet,
        "suggested_fix": finding.suggested_fix,
        "severity": finding.severity,
    }

    return Narrative(
        headline=headline.format_map(fmt_vars),
        risk_summary=risk.format_map(fmt_vars),
    )
