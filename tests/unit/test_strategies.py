import pytest

from credweaver.core.profile import DateInfo, Profile
from credweaver.strategies.common_passwords import CommonPasswordsStrategy
from credweaver.strategies.concatenation import ConcatenationStrategy
from credweaver.strategies.date_based import DateBasedStrategy
from credweaver.strategies.keyboard_patterns import KeyboardPatternsStrategy


@pytest.fixture
def full_profile():
    return Profile(
        name="alice",
        surname="smith",
        birthdate=DateInfo(day=1, month=3, year=1985),
        pet_name="fluffy",
        company="techcorp",
    )


@pytest.fixture
def minimal_profile():
    return Profile(name="bob")


class TestConcatenationStrategy:
    def test_yields_single_tokens(self, fast_config, full_profile):
        s = ConcatenationStrategy(fast_config)
        results = list(s.generate(full_profile))
        # Profile tokens should appear as single entries or within combinations
        tokens = full_profile.to_tokens()
        for t in tokens:
            assert any(t in r for r in results)

    def test_yields_combinations(self, fast_config, full_profile):
        s = ConcatenationStrategy(fast_config)
        results = set(s.generate(full_profile))
        # Should generate more than just single tokens
        assert len(results) > len(full_profile.to_tokens())

    def test_respects_min_length(self, fast_config, full_profile):
        s = ConcatenationStrategy(fast_config)
        for r in s.generate(full_profile):
            assert len(r) >= fast_config.filters.min_length

    def test_respects_max_length(self, fast_config, full_profile):
        s = ConcatenationStrategy(fast_config)
        for r in s.generate(full_profile):
            assert len(r) <= fast_config.filters.max_length

    def test_empty_profile_yields_nothing(self, fast_config):
        s = ConcatenationStrategy(fast_config)
        results = list(s.generate(Profile()))
        assert results == []

    def test_minimal_profile(self, fast_config, minimal_profile):
        s = ConcatenationStrategy(fast_config)
        results = list(s.generate(minimal_profile))
        assert len(results) >= 1


class TestDateBasedStrategy:
    def test_no_dates_yields_nothing(self, fast_config, minimal_profile):
        s = DateBasedStrategy(fast_config)
        results = list(s.generate(minimal_profile))
        assert results == []

    def test_yields_date_combinations(self, fast_config, full_profile):
        s = DateBasedStrategy(fast_config)
        results = list(s.generate(full_profile))
        assert len(results) > 0
        # Should contain year somewhere
        assert any("1985" in r or "85" in r for r in results)

    def test_combined_with_token(self, fast_config, full_profile):
        s = DateBasedStrategy(fast_config)
        results = list(s.generate(full_profile))
        assert any("alice" in r for r in results)


class TestKeyboardPatternsStrategy:
    def test_yields_common_patterns(self, fast_config, full_profile):
        s = KeyboardPatternsStrategy(fast_config)
        results = list(s.generate(full_profile))
        assert any(p in results for p in ["qwerty", "123456", "password"])

    def test_yields_combined_patterns(self, fast_config, full_profile):
        s = KeyboardPatternsStrategy(fast_config)
        results = list(s.generate(full_profile))
        # Should combine token + pattern
        assert any("alice" in r for r in results)

    def test_respects_length_filter(self, fast_config, full_profile):
        s = KeyboardPatternsStrategy(fast_config)
        for r in s.generate(full_profile):
            assert fast_config.filters.min_length <= len(r) <= fast_config.filters.max_length


class TestCommonPasswordsStrategy:
    def test_yields_common_passwords(self, fast_config, full_profile):
        s = CommonPasswordsStrategy(fast_config)
        results = list(s.generate(full_profile))
        assert any(p in results for p in ["password", "123456", "admin"])

    def test_combines_with_profile(self, fast_config, full_profile):
        s = CommonPasswordsStrategy(fast_config)
        results = list(s.generate(full_profile))
        assert any("alice" in r for r in results)

    def test_empty_profile_still_yields_common(self, fast_config):
        s = CommonPasswordsStrategy(fast_config)
        results = list(s.generate(Profile()))
        assert len(results) > 0
