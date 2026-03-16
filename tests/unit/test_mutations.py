import pytest

from credweaver.config.schema import AppendConfig, CaseConfig, LeetConfig, MutationConfig
from credweaver.mutations.append import AppendMutation
from credweaver.mutations.case import CaseMutation
from credweaver.mutations.leet import LeetMutation


@pytest.fixture
def mut_config():
    return MutationConfig(
        leet=LeetConfig(enabled=True, level=1),
        case=CaseConfig(modes=["lower", "upper", "title"]),
        append=AppendConfig(numbers=True, numbers_range=(0, 5), symbols=["!"], years=False),
    )


def test_leet_level1(mut_config):
    mut = LeetMutation(mut_config)
    results = list(mut.apply("password"))
    assert "password" in results
    assert "p@ssw0rd" in results or any("0" in r for r in results)


def test_leet_disabled():
    cfg = MutationConfig(leet=LeetConfig(enabled=False, level=1))
    mut = LeetMutation(cfg)
    results = list(mut.apply("hello"))
    assert results == ["hello"]


def test_case_mutations(mut_config):
    mut = CaseMutation(mut_config)
    results = list(mut.apply("hello"))
    assert "hello" in results
    assert "HELLO" in results
    assert "Hello" in results


def test_append_numbers(mut_config):
    mut = AppendMutation(mut_config)
    results = list(mut.apply("test"))
    assert "test0" in results
    assert "test5" in results
    assert "test!" in results


def test_append_no_numbers():
    cfg = MutationConfig(append=AppendConfig(numbers=False, symbols=[], years=False))
    mut = AppendMutation(cfg)
    results = list(mut.apply("test"))
    assert results == ["test"]
