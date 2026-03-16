import yaml
from pathlib import Path
from cupp.core.profile import Profile


def load_profile_yaml(path: Path) -> Profile:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Profile.model_validate(data)
