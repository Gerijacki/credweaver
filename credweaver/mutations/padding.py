from collections.abc import Iterator

from credweaver.mutations.base import Mutation


class PaddingMutation(Mutation):
    name = "padding"
    _PADS = ["!", "!!", "!!!", "123", "1234", "@", "##", "***"]

    def apply(self, password: str) -> Iterator[str]:
        if not self.config.padding:
            yield password
            return
        yield password
        for pad in self._PADS:
            yield f"{password}{pad}"
            yield f"{pad}{password}"
            yield f"{pad}{password}{pad}"
