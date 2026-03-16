# Plugin System

## Overview

CUPP v2 uses a self-registering plugin system for generation strategies.
Any Python class that:
1. Inherits from `cupp.strategies.base.Strategy`
2. Is decorated with `@register("strategy_name")`
3. Is imported before `load_enabled_strategies` is called

will be available as a strategy.

## Writing a Custom Strategy

### Step 1: Create the strategy module

```python
# my_strategies/company_patterns.py

from typing import Iterator
from cupp.strategies.base import Strategy
from cupp.strategies.registry import register
from cupp.core.profile import Profile


@register("company_patterns")
class CompanyPatternsStrategy(Strategy):
    """Generates passwords from company name patterns."""

    description = "Company-specific password patterns"

    def generate(self, profile: Profile) -> Iterator[str]:
        if not profile.company:
            return

        company = profile.company
        ml = self.config.filters.min_length
        xl = self.config.filters.max_length

        # Common company password patterns
        patterns = [
            company,
            f"{company}123",
            f"{company}!",
            f"{company}2024",
            f"{company}@{company}",
            company.upper(),
            company.capitalize() + "123",
        ]

        for p in patterns:
            if ml <= len(p) <= xl:
                yield p

        # Combine with profile name
        if profile.name:
            for sep in ["", "_", "."]:
                for candidate in [
                    f"{profile.name}{sep}{company}",
                    f"{company}{sep}{profile.name}",
                ]:
                    if ml <= len(candidate) <= xl:
                        yield candidate
```

### Step 2: Register it in your config

```yaml
strategies:
  enabled:
    - concatenation
    - date_based
    - keyboard_patterns
    - common_passwords
    - company_patterns   # ← your new strategy
```

### Step 3: Ensure the module is imported

The strategy module must be imported before `load_enabled_strategies` runs.
There are two ways to achieve this:

**Option A**: Add the import to `cupp/strategies/registry.py` in the
`load_enabled_strategies` function:

```python
def load_enabled_strategies(config: CuppConfig) -> list[Strategy]:
    from cupp.strategies import concatenation, date_based, keyboard_patterns, common_passwords
    from my_strategies import company_patterns  # ← add this
    return [get_strategy(name, config) for name in config.strategies.enabled]
```

**Option B**: Import the module in your calling code before generating:

```python
from my_strategies import company_patterns  # triggers @register
from cupp import Engine
from cupp.core.profile import Profile

engine = Engine()
profile = Profile(company="acme", name="john")
for p in engine.generate(profile):
    print(p)
```

## Strategy API Reference

### `Strategy` base class

```python
class Strategy(ABC):
    name: str                      # set by @register decorator
    description: str = ""         # human-readable description

    def __init__(self, config: CuppConfig): ...

    @abstractmethod
    def generate(self, profile: Profile) -> Iterator[str]: ...
```

The `generate` method must be a generator function or return any `Iterator[str]`.
It should respect `self.config.filters.min_length` and `self.config.filters.max_length`.

### Available config fields

Inside a strategy, `self.config` provides:

```python
self.config.generation.separators      # list of separator strings
self.config.generation.max_depth       # max combination depth
self.config.filters.min_length         # minimum password length
self.config.filters.max_length         # maximum password length
self.config.mutations.leet.level       # leet substitution level
self.config.mutations.case.modes       # list of case mode names
self.config.mutations.append.numbers   # bool: append numbers
self.config.mutations.append.numbers_range  # (lo, hi) tuple
self.config.mutations.append.symbols   # list of symbols
self.config.mutations.append.years     # bool: append years
```

### `TokenExtractor`

Use `TokenExtractor` inside your strategy to derive normalized tokens:

```python
from cupp.core.token_extractor import TokenExtractor

extractor = TokenExtractor()
tokens = extractor.extract(profile)
# tokens = {"base": [...], "dates": [...], "all": [...]}

all_tokens = extractor.extract_with_variations(profile)
# includes original, capitalized, upper, reversed, truncated versions
```

## Registry API

```python
from cupp.strategies.registry import (
    register,           # decorator
    get_strategy,       # instantiate by name
    list_strategies,    # list registered names
    load_enabled_strategies,  # instantiate all enabled
    _REGISTRY,          # dict[str, type[Strategy]]
)
```

### `register(name: str)` decorator

Registers the decorated class under `name`. Sets `cls.name = name`.

### `get_strategy(name: str, config: CuppConfig) -> Strategy`

Instantiates the strategy registered under `name`.
Raises `KeyError` if the strategy is not registered.

### `list_strategies() -> list[str]`

Returns the names of all currently registered strategies.

### `load_enabled_strategies(config: CuppConfig) -> list[Strategy]`

Imports all built-in strategy modules (to trigger `@register`), then
instantiates and returns strategies for each name in
`config.strategies.enabled`.

## Example: Password Spray List Strategy

A strategy that generates passwords common in enterprise password spray attacks:

```python
@register("spray_list")
class SprayListStrategy(Strategy):
    description = "Enterprise password spray patterns"

    _PATTERNS = [
        "Welcome1", "Welcome1!", "Welcome123", "Password1",
        "Summer2024", "Winter2024", "Spring2024", "Fall2024",
        "Company1", "January2024", "February2024",
    ]

    def generate(self, profile: Profile) -> Iterator[str]:
        ml = self.config.filters.min_length
        xl = self.config.filters.max_length

        for p in self._PATTERNS:
            if ml <= len(p) <= xl:
                yield p

        # Substitute company name
        if profile.company:
            company = profile.company.capitalize()
            for p in self._PATTERNS:
                substituted = p.replace("Company", company)
                if substituted != p and ml <= len(substituted) <= xl:
                    yield substituted
```

## Testing Custom Strategies

```python
# tests/test_spray_list.py
from cupp.config.loader import load_config
from my_strategies.spray_list import SprayListStrategy
from cupp.core.profile import Profile

def test_spray_list_generates():
    config = load_config()
    strategy = SprayListStrategy(config)
    profile = Profile(company="acme")
    results = list(strategy.generate(profile))
    assert len(results) > 0
    assert "Welcome1" in results
    assert all(
        config.filters.min_length <= len(r) <= config.filters.max_length
        for r in results
    )
```
