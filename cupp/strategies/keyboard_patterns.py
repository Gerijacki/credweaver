from typing import Iterator
from cupp.strategies.base import Strategy
from cupp.strategies.registry import register
from cupp.core.profile import Profile
from cupp.config.defaults import KEYBOARD_PATTERNS


@register("keyboard_patterns")
class KeyboardPatternsStrategy(Strategy):
    description = "Generates keyboard walk patterns combined with profile tokens"

    def generate(self, profile: Profile) -> Iterator[str]:
        from cupp.core.token_extractor import TokenExtractor
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
