from collections.abc import Iterator

from credweaver.core.profile import Profile
from credweaver.strategies.base import Strategy
from credweaver.strategies.registry import register


@register("date_based")
class DateBasedStrategy(Strategy):
    description = "Generates passwords combining tokens with date variations"

    def generate(self, profile: Profile) -> Iterator[str]:
        from credweaver.core.token_extractor import TokenExtractor

        base_tokens = TokenExtractor().extract(profile)["base"]
        date_tokens = profile.to_date_tokens()

        if not date_tokens:
            return

        for base in base_tokens:
            for date in date_tokens:
                for sep in ["", "_", "-"]:
                    for candidate in [f"{base}{sep}{date}", f"{date}{sep}{base}"]:
                        ml = self.config.filters.min_length
                        xl = self.config.filters.max_length
                        if ml <= len(candidate) <= xl:
                            yield candidate
