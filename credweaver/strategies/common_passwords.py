from collections.abc import Iterator

from credweaver.config.defaults import TOP_COMMON_PASSWORDS
from credweaver.core.profile import Profile
from credweaver.strategies.base import Strategy
from credweaver.strategies.registry import register


@register("common_passwords")
class CommonPasswordsStrategy(Strategy):
    description = "Combines common passwords with profile tokens"

    def generate(self, profile: Profile) -> Iterator[str]:
        from credweaver.core.token_extractor import TokenExtractor

        tokens = TokenExtractor().extract(profile)["base"]
        ml = self.config.filters.min_length
        xl = self.config.filters.max_length

        for p in TOP_COMMON_PASSWORDS:
            if ml <= len(p) <= xl:
                yield p

        for token in tokens:
            for common in TOP_COMMON_PASSWORDS:
                for candidate in [f"{token}{common}", f"{common}{token}"]:
                    if ml <= len(candidate) <= xl:
                        yield candidate
