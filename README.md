# Crystal Ball ◇

**Deterministic pre-commit security checks that spot risky code before it lands.**

## What Problem It Solves

Security mistakes often slip in during fast iteration: hardcoded secrets, unsafe patterns, and risky code paths that look harmless in a diff. Most checks run later in CI, after the commit is already shared.

Crystal Ball moves that feedback to commit time. It scans only what you staged, flags risky patterns with clear severity, and blocks commits when the risk is high enough to matter.

## Key Features

- Deterministic, offline analysis (no external APIs)
- AST-based static analysis for Python code
- Git pre-commit hook integration via `crystal install`
- Staged-file scanning only (fast, focused feedback)
- Diff-aware mode to evaluate changed lines
- Severity grading with commit blocking for `HIGH` and `CRITICAL`
- Bypass support with standard Git escape hatch: `--no-verify`
- Multiple deterministic output tones:
  - `oracle`
  - `dramatic`
  - `professional`
  - `minimalist`
- GitHub Actions annotation mode with `--github`
- CI-friendly and reproducible results

## How It Works

### Git pre-commit hook integration

`crystal install` registers Crystal Ball in your repository’s pre-commit flow. On each `git commit`, the hook runs automatically before the commit is finalized.

### Diff-aware scanning

Crystal Ball inspects staged files and can focus on changed lines, reducing noise from untouched legacy code and keeping feedback relevant to the current commit.

### Severity-based blocking

Findings are classified by severity. `HIGH` and `CRITICAL` findings fail the hook and stop the commit. Lower-severity findings are reported without blocking.

### Deterministic formatter system

Results are rendered through deterministic formatter profiles (`oracle`, `dramatic`, `professional`, `minimalist`) so output style can match your workflow while preserving consistent technical results.

## Installation

```bash
# From your Python environment
pip install crystal-ball
```

```bash
# In your repository: install the Git hook
crystal install
```

## Usage Examples

```bash
# Install Git pre-commit hook
crystal install
```

```bash
# Scan one file directly
crystal scan file.py
```

```bash
# Scan staged changes
crystal scan-staged
```

```bash
# Normal commit flow (hook runs automatically)
git commit -m "Add payment validation"
```

If Crystal Ball detects `HIGH` or `CRITICAL` findings in staged changes, the commit is blocked and findings are printed with severity and location.

```bash
# Bypass hook intentionally (not recommended for routine use)
git commit -m "Emergency hotfix" --no-verify
```

Use `--no-verify` only when you explicitly accept the risk or need a temporary escape hatch.

## GitHub Actions Integration

Crystal Ball supports GitHub annotation output for CI with the `--github` flag.

```bash
crystal scan-staged --github
```

In GitHub Actions, this format can surface findings directly in the PR/commit UI as annotations, making review faster without external services.

## Example Output

```text
Crystal Ball (professional mode)
Scanning staged files...
- src/config.py
- src/auth/session.py

[HIGH] Potential hardcoded secret
  File: src/config.py:18
  Rule: hardcoded-secret
  Snippet: API_KEY = "prod_live_..."

[MEDIUM] Dynamic code execution pattern
  File: src/auth/session.py:42
  Rule: dynamic-exec
  Snippet: eval(user_input)

Result: 1 HIGH, 1 MEDIUM
Commit blocked due to HIGH/CRITICAL findings.
Use --no-verify to bypass.
```

## Architecture Overview

- **CLI layer**: command entry points (`install`, `scan`, `scan-staged`)
- **Git integration**: staged file discovery and pre-commit hook wiring
- **Diff engine**: changed-line filtering for focused analysis
- **Detector engine**: AST-based static rules and severity classification
- **Formatter/reporter**: deterministic tone-based output and optional GitHub annotations

## Why It’s Different

- **Commit-time focus**: catches risk before code leaves your machine
- **Deterministic behavior**: repeatable results, stable in local and CI environments
- **Offline-first**: no network dependency, no API credentials, no data egress
- **Practical guardrails**: blocks only on high-impact findings, supports explicit bypass when needed
- **Readable output**: same findings, selectable communication style for different teams

## Roadmap / Future Improvements

- Expand built-in rule coverage (framework-specific security checks)
- Add project-level config for severity thresholds and rule toggles
- Improve language and file-type coverage beyond core Python workflows
- Add baseline/suppression mechanics for gradual adoption in legacy repos
- Publish richer CI templates for common pipelines

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
