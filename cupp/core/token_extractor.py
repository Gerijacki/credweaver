from cupp.core.profile import Profile


class TokenExtractor:
    """Extracts and normalizes tokens from a Profile for generation."""

    def extract(self, profile: Profile) -> dict[str, list[str]]:
        base = profile.to_tokens()
        dates = profile.to_date_tokens()
        return {
            "base": list(set(base)),
            "dates": list(set(dates)),
            "all": list(set(base + dates)),
        }

    def extract_with_variations(self, profile: Profile) -> list[str]:
        tokens = profile.to_tokens()
        variations: set[str] = set(tokens)
        for t in tokens:
            variations.add(t.capitalize())
            variations.add(t.upper())
            variations.add(t[::-1])
            if len(t) > 3:
                variations.add(t[:3])
        variations.update(profile.to_date_tokens())
        return list(variations)
