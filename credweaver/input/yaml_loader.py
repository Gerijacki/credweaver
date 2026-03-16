from pathlib import Path

import yaml  # type: ignore[import-untyped]

from credweaver.core.profile import Profile


def load_profile_yaml(path: Path) -> Profile:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Profile.model_validate(data)
