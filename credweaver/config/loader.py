from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from credweaver.config.defaults import DEFAULT_CONFIG_YAML
from credweaver.config.schema import CredWeaverConfig


def load_config(path: Path | None = None) -> CredWeaverConfig:
    if path is None:
        data = yaml.safe_load(DEFAULT_CONFIG_YAML)
    else:
        with open(path) as f:
            data = yaml.safe_load(f)
    return CredWeaverConfig.model_validate(data)


def merge_config(base: CredWeaverConfig, overrides: dict[str, Any]) -> CredWeaverConfig:
    base_dict = base.model_dump()
    _deep_merge(base_dict, overrides)
    return CredWeaverConfig.model_validate(base_dict)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
