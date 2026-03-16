from collections.abc import Iterator
from itertools import product

from credweaver.core.profile import Profile
from credweaver.strategies.base import Strategy
from credweaver.strategies.registry import register


@register("concatenation")
class ConcatenationStrategy(Strategy):
    description = "Combines profile tokens with separators at various depths"

    def generate(self, profile: Profile) -> Iterator[str]:
        from credweaver.core.token_extractor import TokenExtractor

        tokens = TokenExtractor().extract_with_variations(profile)
        if not tokens:
            return
        seps = self.config.generation.separators
        max_depth = self.config.generation.max_depth

        # Depth 1: single tokens
        for t in tokens:
            if self.config.filters.min_length <= len(t) <= self.config.filters.max_length:
                yield t

        # Depth 2+: combinations
        for depth in range(2, min(max_depth + 1, len(tokens) + 1)):
            for combo in product(tokens, repeat=depth):
                if len(set(combo)) < depth:  # avoid "john+john"
                    continue
                for sep in seps:
                    candidate = sep.join(combo)
                    if (
                        self.config.filters.min_length
                        <= len(candidate)
                        <= self.config.filters.max_length
                    ):
                        yield candidate
