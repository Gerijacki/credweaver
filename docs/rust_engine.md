# Rust Engine Documentation

## Overview

The Rust engine (`credweaver_engine`) is a compiled Python extension module that
accelerates the most CPU-intensive parts of CredWeaver:

- Cartesian-product combination generation
- Mutation application (leet, case, append)
- Bloom filter deduplication
- Shannon entropy scoring
- Markov chain password generation

The extension is built with [maturin](https://github.com/PyO3/maturin) using
PyO3 0.21 bindings.

## Building

```bash
# Install maturin
pip install maturin

# Development build (installs into current venv)
maturin develop

# Release build
maturin develop --release

# Build wheel
maturin build --release
```

## Module Structure

```
rust_engine/src/
├── lib.rs         PyO3 module definition, Python-facing classes and functions
├── combinator.rs  Lazy Cartesian-product combinator
├── mutations.rs   All mutation types (leet, case, append)
├── dedup.rs       Bloom filter and HashSet deduplication
├── entropy.rs     Shannon entropy and strength scoring
├── markov.rs      Markov chain password generator
└── generator.rs   PasswordGenerator orchestrator struct
```

## Python API

### `generate_combinations(tokens: list[str], config: dict) -> CombinationIterator`

Returns a Python-iterable `CombinationIterator` that lazily yields passwords.
The iterator applies combinations + mutations + deduplication in a single pass.

**Config dict keys:**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `separators` | `list[str]` | `["", "_", "-", "."]` | Token separators |
| `max_depth` | `int` | `3` | Maximum combination depth |
| `min_length` | `int` | `6` | Minimum output length |
| `max_length` | `int` | `20` | Maximum output length |
| `leet_level` | `int` | `2` | Leet substitution level (0=off, 1-3) |
| `case_modes` | `list[str]` | `["lower","title","upper"]` | Case modes to apply |
| `append_numbers` | `bool` | `True` | Append/prepend numbers |
| `number_range` | `list[int]` | `[0, 99]` | Number range [lo, hi] |
| `append_symbols` | `list[str]` | `["!", "@", "#"]` | Symbols to append |
| `append_years` | `list[int]` | `[]` | Years to append |
| `use_bloom` | `bool` | `True` | Enable bloom deduplication |
| `bloom_capacity` | `int` | `10000000` | Bloom filter capacity |

**Example:**

```python
import credweaver_engine

tokens = ["john", "doe", "1990"]
config = {
    "separators": ["", "_"],
    "max_depth": 2,
    "min_length": 6,
    "max_length": 16,
    "leet_level": 2,
    "case_modes": ["lower", "title"],
    "append_numbers": True,
    "number_range": [0, 99],
    "append_symbols": ["!"],
    "append_years": [],
    "use_bloom": True,
    "bloom_capacity": 1_000_000,
}

for password in credweaver_engine.generate_combinations(tokens, config):
    print(password)
```

### `apply_mutations(passwords: list[str], config: dict) -> MutationIterator`

Returns a `MutationIterator` that lazily applies mutations to each input password.

**Config dict keys:** same as `generate_combinations` (only mutation-related keys
are used: `leet_level`, `case_modes`, `append_numbers`, `number_range`,
`append_symbols`, `append_years`, `min_length`, `max_length`).

```python
passwords = ["john", "doe"]
config = {"leet_level": 1, "case_modes": ["lower", "upper"], "append_numbers": False,
          "number_range": [0, 0], "append_symbols": [], "append_years": [],
          "min_length": 4, "max_length": 20}

for mutated in credweaver_engine.apply_mutations(passwords, config):
    print(mutated)
```

### `deduplicate(passwords: list[str]) -> list[str]`

Exact deduplication using a HashSet. Returns a new list with duplicates removed.
Order is not guaranteed to be preserved.

```python
unique = credweaver_engine.deduplicate(["john", "doe", "john", "rex"])
# → ["john", "doe", "rex"]  (order may vary)
```

### `entropy_score(password: str) -> float`

Returns the Shannon entropy (bits) of a single password string.

```python
score = credweaver_engine.entropy_score("P@ssw0rd!")
# → ~2.94 bits
```

### `batch_entropy_score(passwords: list[str]) -> list[tuple[str, float]]`

Scores a list of passwords in parallel using rayon. Returns list of
`(password, entropy)` tuples, unsorted.

```python
scores = credweaver_engine.batch_entropy_score(["abc", "P@ssw0rd!", "password"])
```

### `markov_generate(seed_tokens: list[str], length: int, count: int) -> list[str]`

Trains a bigram Markov chain on the seed tokens and generates `count` passwords
of at most `length` characters.

```python
passwords = credweaver_engine.markov_generate(["john", "doe", "johnny"], 8, 20)
```

## CombinationIterator

A Python class (`__iter__` + `__next__`) wrapping the Rust `PasswordIterator`.
It is single-pass: once exhausted it does not reset.

```python
it = credweaver_engine.generate_combinations(tokens, config)
for p in it:
    process(p)
```

## MutationIterator

Same protocol as `CombinationIterator` but wraps the mutation-only pipeline.

## Combinator Internals

The `Combinator` in `combinator.rs` implements lazy Cartesian permutations:

- For depth D and N tokens, it generates P(N, D) = N!/(N-D)! permutations
- Each permutation is combined with each separator
- The iteration order is: all depth-1 combinations, then all depth-2, etc.
- The `nth_permutation(n, k, index)` function converts a linear index to the
  corresponding permutation, enabling stateless resumption

No permutation list is stored in memory. State is a single integer `perm_index`.

## Bloom Filter Internals

The `BloomFilter` in `dedup.rs` uses:

- Bit array stored as `Vec<u64>` (64 bits per word)
- Two independent hash functions: FNV-1a and DJB2
- k hash positions derived by linear combination: `h1 + i * h2` for i in 0..k
- Optimal k calculated as `(size / capacity) * ln(2)`

With default settings (10M capacity, 0.1% error rate):
- Size ≈ 143,775,476 bits ≈ 17 MB
- k ≈ 10 hash functions

## Entropy Module

Shannon entropy is calculated as:

```
H(X) = -Σ p(x) * log₂(p(x))
```

where p(x) is the frequency of character x in the password string.

`strength_score` combines Shannon entropy (60% weight) with charset-based
entropy (40% weight), both normalized to [0.0, 1.0].

## Markov Chain Internals

The `MarkovChain` builds a transition table from character bigrams:

```
"john" → {"jo": {"h": 1}, "oh": {"n": 1}}
```

Generation uses a seeded LCG (Linear Congruential Generator) for deterministic
output given a fixed seed. Batch generation dispatches each seed to a separate
rayon thread via `into_par_iter()`.

## Performance Notes

- The Rust engine is 5-15x faster than the Python fallback for typical workloads
- Parallelism via rayon is used in: `rank_passwords_parallel`, `batch_score`,
  `generate_batch_parallel` in the Markov module
- The main `PasswordIterator` is single-threaded but allocation-efficient
- For maximum throughput, use `--preset aggressive` with the Rust engine enabled
