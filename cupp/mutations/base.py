from abc import ABC, abstractmethod
from typing import Iterator
from cupp.config.schema import MutationConfig


class Mutation(ABC):
    name: str = "base"

    def __init__(self, config: MutationConfig):
        self.config = config

    @abstractmethod
    def apply(self, password: str) -> Iterator[str]:
        """Yield all mutations of the given password."""
        ...
