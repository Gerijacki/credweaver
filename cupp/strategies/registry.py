from cupp.strategies.base import Strategy
from cupp.config.schema import CuppConfig

_REGISTRY: dict[str, type[Strategy]] = {}


def register(name: str):
    def decorator(cls: type[Strategy]) -> type[Strategy]:
        cls.name = name
        _REGISTRY[name] = cls
        return cls
    return decorator


def get_strategy(name: str, config: CuppConfig) -> Strategy:
    if name not in _REGISTRY:
        raise KeyError(f"Strategy '{name}' not registered. Available: {list(_REGISTRY)}")
    return _REGISTRY[name](config)


def list_strategies() -> list[str]:
    return list(_REGISTRY.keys())


def load_enabled_strategies(config: CuppConfig) -> list[Strategy]:
    # Import all strategy modules to trigger registration
    from cupp.strategies import concatenation, date_based, keyboard_patterns, common_passwords  # noqa: F401
    return [get_strategy(name, config) for name in config.strategies.enabled]
