from typing import Iterator
from cupp.mutations.base import Mutation
from cupp.config.schema import MutationConfig

LEET_LEVEL1: dict[str, list[str]] = {
    "a": ["@"],
    "e": ["3"],
    "i": ["1"],
    "o": ["0"],
    "s": ["5"],
}
LEET_LEVEL2: dict[str, list[str]] = {
    **LEET_LEVEL1,
    "a": ["@", "4"],
    "t": ["7"],
    "g": ["9"],
    "b": ["8"],
}
LEET_LEVEL3: dict[str, list[str]] = {
    **LEET_LEVEL2,
    "l": ["1"],
    "z": ["2"],
    "h": ["#"],
}


class LeetMutation(Mutation):
    name = "leet"

    def __init__(self, config: MutationConfig):
        super().__init__(config)
        level = config.leet.level
        if level >= 3:
            self._map = LEET_LEVEL3
        elif level >= 2:
            self._map = LEET_LEVEL2
        else:
            self._map = LEET_LEVEL1

    def apply(self, password: str) -> Iterator[str]:
        yield password  # original always included
        if not self.config.leet.enabled:
            return
        # Generate one leet variant (most common substitutions)
        result = password
        for char, replacements in self._map.items():
            result = result.replace(char, replacements[0])
        if result != password:
            yield result
        # For level 3, generate all combinations recursively
        if self.config.leet.level >= 3:
            yield from self._all_leet_combos(password)

    def _all_leet_combos(self, password: str) -> Iterator[str]:
        """Generate all possible leet combinations recursively."""
        if not password:
            yield ""
            return
        char = password[0].lower()
        rest_gen = list(self._all_leet_combos(password[1:]))
        variants = [password[0]] + self._map.get(char, [])
        for v in variants:
            for rest in rest_gen:
                combo = v + rest
                if combo != password:
                    yield combo
