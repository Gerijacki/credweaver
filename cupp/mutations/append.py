from typing import Iterator
from cupp.mutations.base import Mutation


class AppendMutation(Mutation):
    name = "append"

    def apply(self, password: str) -> Iterator[str]:
        cfg = self.config.append
        yield password

        if cfg.numbers:
            lo, hi = cfg.numbers_range
            for n in range(lo, hi + 1):
                yield f"{password}{n}"
                if n > 0:
                    yield f"{n}{password}"

        for sym in cfg.symbols:
            yield f"{password}{sym}"
            yield f"{sym}{password}"

        if cfg.years:
            lo, hi = cfg.years_range
            for year in range(lo, hi + 1):
                yield f"{password}{year}"
                yield f"{password}{str(year)[-2:]}"
