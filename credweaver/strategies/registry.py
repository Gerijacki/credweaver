from collections.abc import Callable

from credweaver.config.schema import CredWeaverConfig
from credweaver.strategies.base import Strategy

_REGISTRY: dict[str, type[Strategy]] = {}


def register(name: str) -> Callable[[type[Strategy]], type[Strategy]]:
    def decorator(cls: type[Strategy]) -> type[Strategy]:
        cls.name = name
        _REGISTRY[name] = cls
        return cls

    return decorator


def get_strategy(name: str, config: CredWeaverConfig) -> Strategy:
    if name not in _REGISTRY:
        raise KeyError(f"Strategy '{name}' not registered. Available: {list(_REGISTRY)}")
    return _REGISTRY[name](config)


def list_strategies() -> list[str]:
    return list(_REGISTRY.keys())


def load_enabled_strategies(config: CredWeaverConfig) -> list[Strategy]:
    # Import all strategy modules to trigger registration
    from credweaver.strategies import (  # noqa: F401
        common_passwords,
        concatenation,
        date_based,
        keyboard_patterns,
    )

    return [get_strategy(name, config) for name in config.strategies.enabled]
