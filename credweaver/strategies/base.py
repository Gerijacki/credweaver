from abc import ABC, abstractmethod
from collections.abc import Iterator

from credweaver.config.schema import CredWeaverConfig
from credweaver.core.profile import Profile


class Strategy(ABC):
    """Base class for all generation strategies."""

    name: str = "base"
    description: str = ""

    def __init__(self, config: CredWeaverConfig):
        self.config = config

    @abstractmethod
    def generate(self, profile: Profile) -> Iterator[str]:
        """Yield candidate passwords for the given profile."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
