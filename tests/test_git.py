"""Tests for crystal_ball.git module."""

import stat
import textwrap

import pytest

from crystal_ball.git import (
    HOOK_SCRIPT,
    ChangedFile,
    _HUNK_RE,
    parse_staged_diff,
    install_hook,
    find_git_root,
    get_staged_files,
    file_too_large,
)


class TestHunkRegex:
    """Validate the diff hunk header regex."""

    def test_single_line_add(self):
        m = _HUNK_RE.match("@@ -0,0 +1 @@")
        assert m
        assert m.group(1) == "1"
        assert m.group(2) is None

    def test_multi_line_add(self):
        m = _HUNK_RE.match("@@ -5,0 +6,3 @@")
        assert m
        assert m.group(1) == "6"
        assert m.group(2) == "3"

    def test_zero_count(self):
        m = _HUNK_RE.match("@@ -1,2 +1,0 @@")
        assert m
        assert m.group(1) == "1"
        assert m.group(2) == "0"

    def test_no_match_on_garbage(self):
        assert _HUNK_RE.match("not a hunk") is None


class TestChangedFile:
    """ChangedFile data structure tests."""

    def test_default_added_lines_is_empty(self):
        cf = ChangedFile(filepath="foo.py")
        assert cf.added_lines == set()

    def test_with_lines(self):
        cf = ChangedFile(filepath="foo.py", added_lines={1, 2, 3})
        assert 2 in cf.added_lines


class TestHookScript:
    """Verify the generated hook script content."""

    def test_hook_calls_scan_staged(self):
        assert "crystal scan-staged" in HOOK_SCRIPT

    def test_hook_is_shell_script(self):
        assert HOOK_SCRIPT.startswith("#!/bin/sh")

    def test_hook_mentions_no_verify(self):
        assert "--no-verify" in HOOK_SCRIPT


class TestInstallHook:
    """Hook installation into .git/hooks/."""

    def test_installs_hook_in_git_repo(self, tmp_path, monkeypatch):
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)
        monkeypatch.setattr("crystal_ball.git.find_git_root", lambda: tmp_path)

        hook_path = install_hook()

        assert hook_path.exists()
        assert hook_path.read_text() == HOOK_SCRIPT
        assert hook_path.stat().st_mode & stat.S_IXUSR

    def test_raises_outside_git_repo(self, monkeypatch):
        monkeypatch.setattr("crystal_ball.git.find_git_root", lambda: None)
        with pytest.raises(RuntimeError, match="Not inside a Git repository"):
            install_hook()


class TestFileTooLarge:
    """Max file size safeguard."""

    def test_small_file_is_ok(self, tmp_path):
        f = tmp_path / "small.py"
        f.write_text("x = 1\n")
        assert file_too_large(str(f)) is False

    def test_nonexistent_file_is_not_too_large(self):
        assert file_too_large("/nonexistent/path") is False
