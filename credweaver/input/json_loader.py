import json
from pathlib import Path

from credweaver.core.profile import Profile


def load_profile_json(path: Path) -> Profile:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return Profile.model_validate(data)
