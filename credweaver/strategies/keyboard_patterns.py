from collections.abc import Iterator

from credweaver.config.defaults import KEYBOARD_PATTERNS
from credweaver.core.profile import Profile
from credweaver.strategies.base import Strategy
from credweaver.strategies.registry import register


@register("keyboard_patterns")
class KeyboardPatternsStrategy(Strategy):
    description = "Generates keyboard walk patterns combined with profile tokens"

    def generate(self, profile: Profile) -> Iterator[str]:
        from credweaver.core.token_extractor import TokenExtractor

        tokens = TokenExtractor().extract(profile)["base"]
        ml = self.config.filters.min_length
        xl = self.config.filters.max_length

        for pattern in KEYBOARD_PATTERNS:
            if ml <= len(pattern) <= xl:
                yield pattern

        for token in tokens:
            for pattern in KEYBOARD_PATTERNS:
                for candidate in [f"{token}{pattern}", f"{pattern}{token}"]:
                    if ml <= len(candidate) <= xl:
                        yield candidate
