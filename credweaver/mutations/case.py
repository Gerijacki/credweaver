from collections.abc import Callable, Iterator

from credweaver.mutations.base import Mutation


class CaseMutation(Mutation):
    name = "case"

    def apply(self, password: str) -> Iterator[str]:
        modes = self.config.case.modes
        seen: set[str] = {password}
        yield password
        ops: dict[str, Callable[[str], str]] = {
            "lower": str.lower,
            "upper": str.upper,
            "title": str.title,
            "toggle": lambda s: "".join(
                c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(s)
            ),
            "camel": lambda s: (
                s[:1].lower() + s[1:].title().replace(" ", "")[1:] if len(s) > 1 else s
            ),
        }
        for mode in modes:
            if mode in ops:
                result = ops[mode](password)
                if result not in seen:
                    seen.add(result)
                    yield result
