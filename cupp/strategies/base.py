from abc import ABC, abstractmethod
from typing import Iterator
from cupp.core.profile import Profile
from cupp.config.schema import CuppConfig


class Strategy(ABC):
    """Base class for all generation strategies."""

    name: str = "base"
    description: str = ""

    def __init__(self, config: CuppConfig):
        self.config = config

    @abstractmethod
    def generate(self, profile: Profile) -> Iterator[str]:
        """Yield candidate passwords for the given profile."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
