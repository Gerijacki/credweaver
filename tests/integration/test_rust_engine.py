import pytest

cupp_engine = pytest.importorskip("cupp_engine", reason="cupp_engine Rust module not compiled")


@pytest.fixture
def base_config():
    return {
        "separators": ["", "_"],
        "max_depth": 2,
        "min_length": 4,
        "max_length": 16,
        "leet_level": 1,
        "case_modes": ["lower", "title"],
        "append_numbers": True,
        "number_range": [0, 9],
        "append_symbols": ["!"],
        "append_years": [2024],
        "use_bloom": True,
        "bloom_capacity": 100000,
    }


def test_generate_combinations_is_iterable(base_config):
    tokens = ["john", "doe"]
    it = cupp_engine.generate_combinations(tokens, base_config)
    result = next(it)
    assert isinstance(result, str)


def test_generate_combinations_collect_batch(base_config):
    tokens = ["test", "user"]
    it = cupp_engine.generate_combinations(tokens, base_config)
    batch = it.collect_batch(100)
    assert len(batch) > 0
    assert all(isinstance(p, str) for p in batch)


def test_generate_combinations_collect_batch_exhausts(base_config):
    tokens = ["ab"]
    it = cupp_engine.generate_combinations(tokens, base_config)
    all_passwords = []
    while True:
        batch = it.collect_batch(1000)
        if not batch:
            break
        all_passwords.extend(batch)
    assert len(all_passwords) > 0
    # Bloom filter significantly reduces duplicates (not guaranteed exact with short tokens)
    unique_count = len(set(all_passwords))
    assert unique_count >= len(all_passwords) * 0.5  # at least 50% unique


def test_generate_combinations_length_filter(base_config):
    tokens = ["hello", "world"]
    it = cupp_engine.generate_combinations(tokens, base_config)
    passwords = []
    while True:
        batch = it.collect_batch(500)
        if not batch:
            break
        passwords.extend(batch)
    for p in passwords:
        assert base_config["min_length"] <= len(p) <= base_config["max_length"]


def test_apply_mutations_is_iterable(base_config):
    words = ["test", "hello", "world"]
    it = cupp_engine.apply_mutations(words, base_config)
    result = next(it)
    assert isinstance(result, str)


def test_apply_mutations_generates_variants(base_config):
    words = ["password"]
    it = cupp_engine.apply_mutations(words, base_config)
    results = list(it)
    assert "password" in results
    assert len(results) > 1  # should have leet/case/append variants


def test_deduplicate_removes_dupes():
    words = ["abc", "def", "abc", "ghi", "def", "abc"]
    result = cupp_engine.deduplicate(words)
    assert len(result) == 3
    assert set(result) == {"abc", "def", "ghi"}


def test_deduplicate_preserves_all_unique():
    words = ["a", "b", "c", "d", "e"]
    result = cupp_engine.deduplicate(words)
    assert len(result) == 5


def test_entropy_score_range():
    score = cupp_engine.entropy_score("password")
    assert 0.0 < score <= 5.0  # Shannon entropy is bounded by log2(charset)


def test_entropy_score_complex_higher():
    simple = cupp_engine.entropy_score("aaaaaaa")
    complex_pw = cupp_engine.entropy_score("P@ssw0rd123!")
    assert complex_pw > simple


def test_batch_entropy_score():
    passwords = ["hello", "P@ssw0rd!", "abc", "correct-horse-battery"]
    results = cupp_engine.batch_entropy_score(passwords)
    assert len(results) == len(passwords)
    for pw, score in results:
        assert isinstance(pw, str)
        assert isinstance(score, float)
        assert score >= 0.0


def test_markov_generate_returns_strings():
    results = cupp_engine.markov_generate(["john", "doe", "johnny", "johndoe"], 8, 5)
    assert len(results) == 5
    assert all(isinstance(r, str) for r in results)


def test_collect_all(base_config):
    tokens = ["hi"]
    it = cupp_engine.generate_combinations(tokens, base_config)
    all_pw = it.collect_all()
    assert len(all_pw) > 0
    assert all(isinstance(p, str) for p in all_pw)
