import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from crystal_ball.cli import app

runner = CliRunner()


class TestCliScan:
    """Tests for the scan command."""

    def test_scan_existing_file(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"x = 1\n")
            f.flush()
            path = Path(f.name)
        try:
            result = runner.invoke(app, ["scan", str(path)])
            assert result.exit_code == 0
        finally:
            path.unlink()

    def test_scan_file_with_findings_exits_1_for_high(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"eval('1')\n")
            f.flush()
            path = Path(f.name)
        try:
            result = runner.invoke(app, ["scan", str(path)])
            assert result.exit_code == 1
        finally:
            path.unlink()

    def test_scan_file_medium_only_exits_0(self):
        code = b"try:\n    x = 1\nexcept:\n    pass\n"
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            path = Path(f.name)
        try:
            result = runner.invoke(app, ["scan", str(path)])
            assert result.exit_code == 0
        finally:
            path.unlink()

    def test_scan_nonexistent_file_fails(self):
        result = runner.invoke(app, ["scan", "/nonexistent/path/file.py"])
        assert result.exit_code == 1
        assert "does not exist" in result.output

    def test_scan_directory_fails(self):
        with tempfile.TemporaryDirectory() as d:
            result = runner.invoke(app, ["scan", d])
            assert result.exit_code == 1
            assert "not a file" in result.output

    def test_scan_multiple_files(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f1:
            f1.write(b"x = 1\n")
            f1.flush()
            path1 = Path(f1.name)
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f2:
            f2.write(b"y = 2\n")
            f2.flush()
            path2 = Path(f2.name)
        try:
            result = runner.invoke(app, ["scan", str(path1), str(path2)])
            assert result.exit_code == 0
        finally:
            path1.unlink()
            path2.unlink()


class TestCliToneFlag:
    """Tests for the --tone / -t flag."""

    def test_scan_help_shows_tone_option(self):
        result = runner.invoke(app, ["scan", "--help"])
        assert result.exit_code == 0
        assert "--tone" in result.output

    def test_default_tone_is_oracle(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"x = 1\n")
            f.flush()
            path = Path(f.name)
        try:
            result = runner.invoke(app, ["scan", str(path)])
            assert result.exit_code == 0
        finally:
            path.unlink()

    @pytest.mark.parametrize("tone", ["oracle", "dramatic", "minimalist", "professional"])
    def test_all_tones_run_without_error(self, tone):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"x = 1\n")
            f.flush()
            path = Path(f.name)
        try:
            result = runner.invoke(app, ["scan", "--tone", tone, str(path)])
            assert result.exit_code == 0
        finally:
            path.unlink()

    def test_short_flag(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"x = 1\n")
            f.flush()
            path = Path(f.name)
        try:
            result = runner.invoke(app, ["scan", "-t", "minimalist", str(path)])
            assert result.exit_code == 0
        finally:
            path.unlink()

    def test_invalid_tone_fails(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"x = 1\n")
            f.flush()
            path = Path(f.name)
        try:
            result = runner.invoke(app, ["scan", "--tone", "pirate", str(path)])
            assert result.exit_code == 1
            assert "unknown tone" in result.output
        finally:
            path.unlink()


class TestCliGithubFlag:
    """Tests for the --github flag."""

    def test_github_flag_emits_annotations(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"eval('1')\n")
            f.flush()
            path = Path(f.name)
        try:
            result = runner.invoke(app, ["scan", "--github", str(path)])
            assert "::error" in result.output or "::warning" in result.output
        finally:
            path.unlink()

    def test_github_flag_clean_file(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"x = 1\n")
            f.flush()
            path = Path(f.name)
        try:
            result = runner.invoke(app, ["scan", "--github", str(path)])
            assert result.exit_code == 0
            assert "::" not in result.output
        finally:
            path.unlink()


class TestCliInstall:
    """Tests for the install command."""

    def test_install_outside_repo_fails(self, monkeypatch):
        monkeypatch.setattr("crystal_ball.cli.find_git_root", lambda: None)
        monkeypatch.setattr(
            "crystal_ball.cli.install_hook",
            lambda: (_ for _ in ()).throw(RuntimeError("Not inside a Git repository")),
        )
        result = runner.invoke(app, ["install"])
        assert result.exit_code == 1
        assert "Not inside a Git repository" in result.output


class TestCliVersion:
    """Tests for the version command."""

    def test_version_output(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestCliHelp:
    """Tests for CLI help."""

    def test_no_args_shows_help(self):
        result = runner.invoke(app, [])
        assert result.exit_code in (0, 2)
        assert "Usage" in result.output

    def test_scan_help(self):
        result = runner.invoke(app, ["scan", "--help"])
        assert result.exit_code == 0
        assert "scan" in result.output

    def test_install_appears_in_help(self):
        result = runner.invoke(app, ["--help"])
        assert "install" in result.output

    def test_scan_staged_appears_in_help(self):
        result = runner.invoke(app, ["--help"])
        assert "scan-staged" in result.output


class TestCliModuleExecution:
    """Test running via python -m crystal_ball."""

    def test_scan_via_module(self):
        """Verify crystal_ball can be run as python -m crystal_ball."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"x = 1\n")
            f.flush()
            path = Path(f.name)
        try:
            result = subprocess.run(
                [sys.executable, "-m", "crystal_ball", "scan", str(path)],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
        finally:
            path.unlink()
