import yaml
from pathlib import Path
from cupp.config.schema import CuppConfig
from cupp.config.defaults import DEFAULT_CONFIG_YAML


def load_config(path: Path | None = None) -> CuppConfig:
    if path is None:
        data = yaml.safe_load(DEFAULT_CONFIG_YAML)
    else:
        with open(path) as f:
            data = yaml.safe_load(f)
    return CuppConfig.model_validate(data)


def merge_config(base: CuppConfig, overrides: dict) -> CuppConfig:
    base_dict = base.model_dump()
    _deep_merge(base_dict, overrides)
    return CuppConfig.model_validate(base_dict)


def _deep_merge(base: dict, override: dict) -> None:
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
