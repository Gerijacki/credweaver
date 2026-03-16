import pytest
from cupp.core.profile import Profile, DateInfo
from cupp.config.loader import load_config
from cupp.config.schema import CuppConfig


@pytest.fixture
def sample_profile() -> Profile:
    return Profile(
        name="john",
        surname="doe",
        nickname="johnny",
        birthdate=DateInfo(day=15, month=6, year=1990),
        partner_name="jane",
        pet_name="rex",
        company="acme",
        keywords=["hacker", "test"],
    )


@pytest.fixture
def default_config() -> CuppConfig:
    return load_config()


@pytest.fixture
def fast_config() -> CuppConfig:
    from cupp.config.loader import merge_config
    cfg = load_config()
    return merge_config(cfg, {
        "generation": {"max_depth": 2, "use_rust_engine": False},
        "mutations": {
            "leet": {"level": 1},
            "case": {"modes": ["lower"]},
            "append": {"numbers_range": [0, 9], "symbols": ["!"], "years": False},
        },
        "filters": {"dedup": False},
    })
