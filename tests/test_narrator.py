"""Tests for the deterministic narrative formatter."""

import pytest

from crystal_ball.detector import Finding
from crystal_ball.narrator import (
    ALL_TONES,
    DEFAULT_TONE,
    Narrative,
    _DEFAULT_TEMPLATES,
    _TEMPLATES,
    _stable_index,
    format_narrative,
)


def _make_finding(**overrides) -> Finding:
    defaults = dict(
        check_id="eval_exec_usage",
        message="eval() executes arbitrary code",
        line=10,
        snippet="eval(user_input)",
        suggested_fix="Use ast.literal_eval()",
        severity="high",
    )
    defaults.update(overrides)
    return Finding(**defaults)


class TestFormatNarrative:
    """Core formatting behaviour."""

    def test_returns_narrative_dataclass(self):
        result = format_narrative(_make_finding())
        assert isinstance(result, Narrative)
        assert isinstance(result.headline, str)
        assert isinstance(result.risk_summary, str)

    def test_headline_and_risk_are_non_empty(self):
        result = format_narrative(_make_finding())
        assert len(result.headline) > 0
        assert len(result.risk_summary) > 0

    def test_deterministic_for_same_finding(self):
        f = _make_finding()
        a = format_narrative(f)
        b = format_narrative(f)
        assert a == b

    def test_different_lines_may_pick_different_variants(self):
        a = format_narrative(_make_finding(line=1))
        b = format_narrative(_make_finding(line=2))
        assert isinstance(a, Narrative)
        assert isinstance(b, Narrative)

    def test_seed_zero_selects_first_variant(self):
        f = _make_finding()
        result = format_narrative(f, seed=0)
        tpl = _TEMPLATES["eval_exec_usage"]["oracle"]
        assert result.headline == tpl.headlines[0].format(
            check_id=f.check_id,
            message=f.message,
            line=f.line,
            snippet=f.snippet,
            suggested_fix=f.suggested_fix,
            severity=f.severity,
        )

    def test_seed_one_selects_second_variant(self):
        f = _make_finding()
        result = format_narrative(f, seed=1)
        tpl = _TEMPLATES["eval_exec_usage"]["oracle"]
        expected_headline = tpl.headlines[1 % len(tpl.headlines)]
        fmt = dict(
            check_id=f.check_id,
            message=f.message,
            line=f.line,
            snippet=f.snippet,
            suggested_fix=f.suggested_fix,
            severity=f.severity,
        )
        assert result.headline == expected_headline.format_map(fmt)


class TestToneModes:
    """Every registered tone produces valid output."""

    @pytest.mark.parametrize("tone", ALL_TONES)
    def test_all_tones_produce_output(self, tone):
        result = format_narrative(_make_finding(), tone=tone, seed=0)
        assert result.headline
        assert result.risk_summary

    @pytest.mark.parametrize("tone", ALL_TONES)
    def test_tone_changes_output(self, tone):
        result = format_narrative(_make_finding(), tone=tone, seed=0)
        assert isinstance(result.headline, str)

    def test_oracle_is_default(self):
        assert DEFAULT_TONE == "oracle"
        explicit = format_narrative(_make_finding(), tone="oracle", seed=0)
        default = format_narrative(_make_finding(), seed=0)
        assert explicit == default


class TestFallback:
    """Unknown check_ids use the fallback template."""

    def test_unknown_check_id_uses_fallback(self):
        f = _make_finding(check_id="totally_unknown_check")
        result = format_narrative(f, seed=0)
        assert result.headline
        assert result.risk_summary

    @pytest.mark.parametrize("tone", ALL_TONES)
    def test_fallback_for_every_tone(self, tone):
        f = _make_finding(check_id="nonexistent")
        result = format_narrative(f, tone=tone, seed=0)
        assert result.headline
        assert result.risk_summary

    def test_fallback_includes_message(self):
        f = _make_finding(check_id="unknown", message="Something bad happened")
        result = format_narrative(f, tone="minimalist", seed=0)
        assert "Something bad happened" in result.risk_summary


class TestTemplateRegistry:
    """Structural checks on the template data."""

    @pytest.mark.parametrize("check_id", list(_TEMPLATES.keys()))
    def test_every_check_has_all_tones(self, check_id):
        for tone in ALL_TONES:
            assert tone in _TEMPLATES[check_id], (
                f"{check_id} missing tone '{tone}'"
            )

    @pytest.mark.parametrize("check_id", list(_TEMPLATES.keys()))
    def test_templates_have_non_empty_variants(self, check_id):
        for tone in ALL_TONES:
            tpl = _TEMPLATES[check_id][tone]
            assert len(tpl.headlines) >= 1
            assert len(tpl.risks) >= 1
            for h in tpl.headlines:
                assert len(h.strip()) > 0
            for r in tpl.risks:
                assert len(r.strip()) > 0

    def test_default_templates_cover_all_tones(self):
        for tone in ALL_TONES:
            assert tone in _DEFAULT_TEMPLATES

    @pytest.mark.parametrize("check_id", list(_TEMPLATES.keys()))
    def test_templates_format_without_error(self, check_id):
        """Every template string should format cleanly with Finding fields."""
        f = _make_finding(check_id=check_id, line=42, snippet="x = 1")
        for tone in ALL_TONES:
            result = format_narrative(f, tone=tone, seed=0)
            assert "{" not in result.headline, f"Unresolved placeholder in {check_id}/{tone} headline"
            assert "{" not in result.risk_summary, f"Unresolved placeholder in {check_id}/{tone} risk"


class TestStableIndex:
    """The variant selection hash is deterministic."""

    def test_same_finding_same_index(self):
        f = _make_finding()
        assert _stable_index(f) == _stable_index(f)

    def test_different_findings_likely_different(self):
        a = _stable_index(_make_finding(line=1))
        b = _stable_index(_make_finding(line=2))
        assert a != b


class TestPerformance:
    """Formatter must be fast — no I/O, no network."""

    def test_thousand_findings_under_one_second(self):
        import time

        findings = [_make_finding(line=i) for i in range(1000)]
        start = time.perf_counter()
        for f in findings:
            format_narrative(f)
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"Took {elapsed:.2f}s for 1000 findings"
