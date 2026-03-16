import pytest
from pydantic import ValidationError
from cupp.config.schema import (
    CuppConfig,
    LeetConfig,
    CaseConfig,
    AppendConfig,
    MutationConfig,
    FilterConfig,
    GenerationConfig,
)
from cupp.config.loader import load_config, merge_config


class TestLeetConfig:
    def test_valid_levels(self):
        for level in [1, 2, 3]:
            cfg = LeetConfig(level=level)
            assert cfg.level == level

    def test_invalid_level_too_low(self):
        with pytest.raises(ValidationError):
            LeetConfig(level=0)

    def test_invalid_level_too_high(self):
        with pytest.raises(ValidationError):
            LeetConfig(level=4)


class TestCaseConfig:
    def test_valid_modes(self):
        cfg = CaseConfig(modes=["lower", "upper", "title", "toggle", "camel"])
        assert len(cfg.modes) == 5

    def test_invalid_mode(self):
        with pytest.raises(ValidationError):
            CaseConfig(modes=["invalid_mode"])

    def test_empty_modes_allowed(self):
        cfg = CaseConfig(modes=[])
        assert cfg.modes == []


class TestFilterConfig:
    def test_min_length_ge_1(self):
        with pytest.raises(ValidationError):
            FilterConfig(min_length=0)

    def test_max_length_le_100(self):
        with pytest.raises(ValidationError):
            FilterConfig(max_length=101)

    def test_valid_lengths(self):
        cfg = FilterConfig(min_length=8, max_length=16)
        assert cfg.min_length == 8
        assert cfg.max_length == 16


class TestLoadConfig:
    def test_load_default(self):
        cfg = load_config()
        assert isinstance(cfg, CuppConfig)
        assert cfg.generation.max_depth == 3
        assert cfg.mutations.leet.level == 2

    def test_load_returns_valid_config(self):
        cfg = load_config()
        assert cfg.filters.min_length < cfg.filters.max_length
        assert len(cfg.strategies.enabled) > 0

    def test_merge_config_overrides(self):
        cfg = load_config()
        merged = merge_config(cfg, {"generation": {"max_depth": 5}})
        assert merged.generation.max_depth == 5
        # Other values unchanged
        assert merged.mutations.leet.level == cfg.mutations.leet.level

    def test_merge_nested_override(self):
        cfg = load_config()
        merged = merge_config(cfg, {"mutations": {"leet": {"level": 1}}})
        assert merged.mutations.leet.level == 1
        # Sibling keys unchanged
        assert merged.mutations.case.modes == cfg.mutations.case.modes

    def test_merge_does_not_mutate_base(self):
        cfg = load_config()
        original_depth = cfg.generation.max_depth
        _ = merge_config(cfg, {"generation": {"max_depth": 5}})
        assert cfg.generation.max_depth == original_depth
