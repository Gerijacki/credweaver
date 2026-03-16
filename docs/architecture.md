# CUPP v2 Architecture

## Project Origin

CUPP v2 is a ground-up redesign of the original [CUpp (Common User Passwords Profiler)](https://github.com/Mebus/cupp) by Mebus. The original project is a single-file Python 2/3 script (~500 lines) that accepts a series of prompted questions about a target and generates a flat wordlist. It was last meaningfully maintained around 2021.

Key limitations of the original that motivated this redesign:

- **Monolithic structure**: all logic in one script; impossible to extend without forking
- **No streaming**: the full wordlist is assembled in a Python list in RAM before writing
- **No validation**: profile input is free-form strings with no type checking
- **No mutation composability**: mutation rules are hardcoded, not pluggable
- **No Rust / performance layer**: pure CPython, bottlenecked at ~500K pass/s
- **No test suite**: zero automated tests
- **No packaging**: no `pyproject.toml`, no installable wheel, no Docker/K8s support

CUPP v2 retains the core concept (profile-driven wordlist generation) while replacing every implementation detail.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI (Typer + Rich)                          │
│   cupp generate | cupp enhance | cupp benchmark | cupp strategies   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      Profile Input       │
                    │  ┌──────────────────┐   │
                    │  │  Interactive     │   │
                    │  │  (Rich prompts)  │   │
                    │  ├──────────────────┤   │
                    │  │  YAML / JSON     │   │
                    │  │  file loader     │   │
                    │  └──────────────────┘   │
                    │  Profile (Pydantic v2)  │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    TokenExtractor        │
                    │  base tokens, date       │
                    │  variants, case/reverse  │
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │              Strategies Layer                │
          │  ┌────────────────────────────────────────┐ │
          │  │  ConcatenationStrategy                 │ │
          │  │  DateBasedStrategy                     │ │
          │  │  KeyboardPatternsStrategy              │ │
          │  │  CommonPasswordsStrategy               │ │
          │  │  (+ any @register'd custom strategies) │ │
          │  └────────────────────────────────────────┘ │
          └──────────────────────┬──────────────────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │       Rust Engine (cupp_engine)              │
          │       or Python Fallback Pipeline            │
          │                                              │
          │  IF use_rust_engine AND cupp_engine present: │
          │  ┌─────────────────────────────────────────┐ │
          │  │  generate_combinations(tokens, config)  │ │
          │  │  ├── Combinator (Cartesian product)     │ │
          │  │  ├── Mutations  (leet × case × append)  │ │
          │  │  └── BloomDedup (probabilistic)         │ │
          │  │  collect_batch(4096) → Vec<String>      │ │
          │  └─────────────────────────────────────────┘ │
          │                                              │
          │  ELSE (Python fallback):                     │
          │  ┌─────────────────────────────────────────┐ │
          │  │  LeetMutation → CaseMutation →          │ │
          │  │  AppendMutation → PaddingMutation       │ │
          │  └─────────────────────────────────────────┘ │
          └──────────────────────┬──────────────────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │                 Filters                      │
          │  filter_length(min, max)                     │
          │  filter_charset(required_charset)  [opt]     │
          │  dedup_stream(bloom_capacity)      [opt]     │
          └──────────────────────┬──────────────────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │                  Output                      │
          │  stream_to_file(path, compress=False/True)   │
          │  GenerationStats (count, elapsed, speed)     │
          └─────────────────────────────────────────────┘
```

## Python Layer

The Python layer owns the user-facing surface and high-level orchestration:

### CLI (`cupp/cli.py`)
Built with [Typer](https://typer.tiangolo.com/) and [Rich](https://github.com/Textualize/rich). Provides five commands: `generate`, `enhance`, `benchmark`, `strategies`, `profile init`, `config`. All heavy work is delegated to the engine layer; the CLI handles argument parsing, progress display, and stats output only.

### Config (`cupp/config/`)
- `schema.py` — Pydantic v2 `BaseModel` classes for every config section: `GenerationConfig`, `LeetConfig`, `CaseConfig`, `AppendConfig`, `MutationConfig`, `FilterConfig`, `StrategyConfig`, `CuppConfig`.
- `defaults.py` — embeds `DEFAULT_CONFIG_YAML` as a string so the tool works with no external config file present.
- `loader.py` — `load_config(path=None)` parses YAML (or falls back to defaults), validates via Pydantic, and returns a `CuppConfig`. `merge_config(base, overrides)` does a deep merge, returning a new `CuppConfig` without mutating the original.

### Profile (`cupp/core/profile.py`)
`Profile` and `DateInfo` are Pydantic v2 models. All string fields are cleaned (stripped, lowercased) by a `field_validator`. `Profile.to_tokens()` returns a flat list of non-null string fields. `Profile.to_date_tokens()` returns all date format variations.

### Token Extractor (`cupp/core/token_extractor.py`)
`TokenExtractor.extract(profile)` returns a dict with keys `base`, `dates`, `all`. `extract_with_variations(profile)` additionally generates case variants (lower, title, upper) and reversed strings for each base token — this is the list passed to the Rust engine.

### Strategies (`cupp/strategies/`)
Self-registering plugins via `@register("name")` decorator. Each strategy receives a `CuppConfig` and returns an `Iterator[str]`. The `load_enabled_strategies(config)` function reads `config.strategies.enabled` and instantiates only those listed. Built-in strategies:

| Strategy | What it generates |
|---|---|
| `concatenation` | Single tokens + pairwise/triple concatenations with separators |
| `date_based` | Token × date-format combinations |
| `keyboard_patterns` | Common keyboard walks × tokens |
| `common_passwords` | Top-N common passwords × token combinations |

### Mutations (`cupp/mutations/`)
Four mutation classes, each implementing `apply(word) -> Iterator[str]`:
- `LeetMutation` — substitutes characters with leet equivalents at 3 levels of aggressiveness
- `CaseMutation` — yields lower, upper, title, toggle, camel variants
- `AppendMutation` — appends numbers (range), symbols, and years to the input word
- `PaddingMutation` — wraps words with symbol padding (enabled by `mutations.padding: true`)

### Filters (`cupp/filters/`)
- `filter_length(stream, min, max)` — generator that drops words outside length bounds
- `filter_charset(stream, required)` — drops words not satisfying charset requirements (e.g. must contain uppercase + digit)
- `dedup_stream(stream, capacity)` — yields each word at most once using a Python Bloom filter

### Output (`cupp/output/`)
- `stream_to_file(stream, path, compress)` — writes to plain text or gzip, using a 1 MB write buffer; returns a `GenerationStats` object
- `GenerationStats` — dataclass with `total_generated`, `elapsed_seconds`, `passwords_per_second`, `output_path`
- `StatsTracker` — context-helper that records start time and computes elapsed on `finish()`

## Rust Layer (`rust_engine/src/`)

The Rust crate is compiled via [maturin](https://github.com/PyO3/maturin) and [PyO3](https://pyo3.rs/). It exposes a Python extension module named `cupp_engine`.

### `lib.rs`
Defines the PyO3 module. Registers all Python-callable functions and classes: `generate_combinations`, `apply_mutations`, `deduplicate`, `entropy_score`, `batch_entropy_score`, `markov_generate`, and the `CombinationIterator` class.

### `generator.rs`
`PasswordGenerator` struct orchestrates the full Rust pipeline: takes tokens + config, drives the combinator, applies multiplicative mutations, runs Bloom dedup, and enforces length filters. `CombinationIterator` is the Python-visible iterator class; it exposes `__next__`, `collect_batch(n)`, and `collect_all()`.

### `combinator.rs`
Implements a lazy Cartesian-product combinator over token lists. Given tokens `["john", "doe"]` and separators `["", "_"]`, it yields all length-1 and length-2 combinations: `john`, `doe`, `johndoe`, `john_doe`, `doejohn`, `doe_john`, etc. Controlled by `max_depth` to cap combinatorial explosion.

### `mutations.rs`
Implements the Rust mutation engine. Unlike the Python pipeline (which applies mutations sequentially), the Rust engine applies them **multiplicatively** — every combination of leet variant × case variant × append suffix is emitted. This is the primary source of Rust's output-volume advantage at higher depths.

### `dedup.rs`
Two dedup implementations:
- `BloomFilter` — a probabilistic bit-array structure; O(1) insert/lookup, fixed memory
- `deduplicate(words)` — exact dedup using `HashSet` from `hashbrown`; used for small input lists only

### `entropy.rs`
Shannon entropy calculation: `H = -Σ p(c) * log2(p(c))` over the character distribution of each password. `entropy_score(word)` returns a float. `batch_entropy_score(words)` returns a list of `(word, score)` pairs efficiently.

### `markov.rs`
Bigram Markov chain trained on a list of seed words. `markov_generate(seeds, max_len, count)` returns `count` new words of at most `max_len` characters, sampled from the learned bigram transition table.

## Python ↔ Rust Integration (PyO3 + Batch FFI Pattern)

Crossing the FFI boundary (Python calling into Rust or Rust returning values to Python) has a non-trivial per-call overhead of ~100–200 ns due to the GIL acquire/release and reference counting. For a pipeline generating millions of passwords, calling `__next__` once per password would add ~200ms of pure FFI overhead per 1M passwords.

The solution is `collect_batch(n)`: a single FFI call that runs the Rust generator for `n` iterations and returns a `Vec<String>` (converted to a Python `list[str]`) in one crossing. CUPP v2 uses a batch size of 4096, reducing FFI crossings by 4096x:

```python
# Pipeline._run_with_rust in cupp/core/pipeline.py
rust_iter = cupp_engine.generate_combinations(tokens, rust_config)
while True:
    batch = rust_iter.collect_batch(4096)  # single FFI call returns 4096 passwords
    if not batch:
        break
    yield from batch                        # pure Python iterator consumption
```

The Rust side holds all generator state between `collect_batch` calls using `PyCell` / interior mutability. No Rust state is serialized to Python between batches.

## Plugin System

Strategies use Python's import-time registration pattern:

```python
# cupp/strategies/registry.py
_REGISTRY: dict[str, type[Strategy]] = {}

def register(name: str):
    def decorator(cls):
        _REGISTRY[name] = cls
        return cls
    return decorator

def load_enabled_strategies(config: CuppConfig) -> list[Strategy]:
    return [_REGISTRY[name](config) for name in config.strategies.enabled if name in _REGISTRY]
```

Adding a new strategy requires only:
1. Creating a module in `cupp/strategies/`
2. Applying `@register("name")` to the class
3. Importing the module (in `registry.py` or in `cli.py`) to trigger registration

No configuration changes or subclass tracking are needed.

## Config System

Configuration is resolved in this order (later overrides earlier):

1. Built-in defaults embedded in `cupp/config/defaults.py` (always available, no file required)
2. User config file (`--config path/to/cupp.yaml`, if provided)
3. CLI preset (`--preset fast|default|aggressive` — each preset is a dict of partial overrides applied via `merge_config`)
4. Programmatic overrides via `merge_config(cfg, {...})`

`merge_config` performs a deep merge: nested dicts are recursively merged, not replaced. Only explicitly provided keys are overridden:

```python
merged = merge_config(base_cfg, {"generation": {"max_depth": 5}})
# merged.generation.max_depth == 5
# merged.generation.use_rust_engine unchanged (still base value)
```

## Pipeline Flow — Step by Step

Given `Profile(name="john", surname="doe", birthdate=DateInfo(day=1, month=1, year=2000))`:

**Step 1 — Token extraction:**
`TokenExtractor.extract_with_variations` produces:
```
base:  ["john", "doe"]
dates: ["01012000", "00", "2000", "0101", "010100", ...]
variations: ["john", "John", "JOHN", "nhoj", "doe", "Doe", "DOE", "eod", ...]
```

**Step 2 — Strategy generation:**
- `ConcatenationStrategy` yields: `"john"`, `"doe"`, `"johndoe"`, `"doejohn"`, `"john_doe"`, `"john-doe"`, ...
- `DateBasedStrategy` yields: `"john01012000"`, `"doe2000"`, `"john00"`, ...
- `KeyboardPatternsStrategy` yields: `"qwerty"`, `"123456"`, `"johnqwerty"`, ...
- `CommonPasswordsStrategy` yields: `"password"`, `"johnpassword"`, ...

**Step 3 — Mutation / Rust engine:**
Each candidate goes through multiplicative mutations (Rust) or sequential mutations (Python):
- `"john"` → leet: `"j0hn"` → case: `"J0HN"` → append: `"J0HN1"`, `"J0HN!"`, ...

**Step 4 — Length filter:**
`filter_length(stream, min_length=6, max_length=20)` drops anything outside bounds.

**Step 5 — Charset filter (optional):**
`filter_charset(stream, ["upper", "digit"])` drops passwords not matching required complexity.

**Step 6 — Dedup:**
`dedup_stream(stream, bloom_capacity=10_000_000)` uses a Bloom filter to drop probable duplicates in O(1) memory per item.

**Step 7 — Output:**
`stream_to_file(stream, Path("wordlist.txt"))` writes to disk with a 1 MB buffer and returns stats.

## Docker / Kubernetes Deployment Architecture

```
┌───────────────────────────────────────────────────────┐
│                  Docker Multi-Stage Build              │
│                                                       │
│  Stage 1: builder (python:3.12-slim + Rust)          │
│   - apt-get: build-essential, pkg-config, libssl-dev  │
│   - rustup install stable                             │
│   - pip install maturin pydantic typer rich           │
│   - maturin build --release → /dist/*.whl             │
│                                                       │
│  Stage 2: runtime (python:3.12-slim)                  │
│   - apt-get: libssl3 only                             │
│   - useradd cupp (non-root)                           │
│   - pip install /dist/*.whl                           │
│   - COPY cupp.yaml + profiles/                        │
│   - ENTRYPOINT ["cupp"]                               │
└───────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────┐
│                Kubernetes Architecture                 │
│                                                       │
│  Namespace: cupp-v2                                   │
│                                                       │
│  ConfigMap: cupp-config ──────────────┐               │
│    cupp.yaml (generation params)      │               │
│                                       ▼               │
│  ConfigMap: cupp-profiles ──► Job / CronJob Pod       │
│    target.yaml                  cupp-v2:latest        │
│                                 /profiles (RO)        │
│  PVC: cupp-output-pvc ──────────/output (RW)          │
│    10Gi ReadWriteOnce                                 │
│                                       │               │
│  Job: cupp-generate ──────────────────┘               │
│    initContainer: profile existence check             │
│    container: cupp generate ...                       │
│    backoffLimit: 2, ttl: 3600s                        │
│                                                       │
│  CronJob: cupp-scheduled                              │
│    schedule: "0 2 * * *"                              │
│    concurrencyPolicy: Forbid                          │
└───────────────────────────────────────────────────────┘
```

## Performance Profile

### When Python fallback is faster (or comparable)

- Very few tokens (≤ 4): The Rust engine's startup cost and FFI round-trip overhead can exceed the actual compute savings for trivially small token sets.
- When `max_depth = 1`: With no cross-token combinations, Python generators running in CPython C are extremely efficient and the speedup from Rust is minimal (~1.2–1.5x).
- When mutation settings are minimal (leet disabled, single case mode, no append): Rust's multiplicative explosion advantage disappears.

### When Rust is faster (5–15x)

- Token count ≥ 6 and `max_depth ≥ 2`: Combinatorial explosion creates tens of thousands of base candidates, and Rust's tight mutation loops (no GC, no dynamic dispatch) dominate.
- Leet level 3 with multiple case modes and a wide number range: This is the regime where Rust generates multiplicative variants (e.g., 8 leet combos × 4 case modes × 100 append suffixes = 3200 variants per base word) whereas Python generates them sequentially (8 + 4 + 100 = 112 variants per base word).
- Batch size 4096: The benefit is fully realized only when `collect_batch(4096)` is used. Reverting to `__next__` reduces the effective speedup to ~1.5x due to FFI overhead dominating.

### Memory

Both Python and Rust paths use constant working memory for generation — no password is held in a list. The Bloom filter is the only memory-scaling component, using approximately `capacity * 10 / log(2)^2` bits (~14 MB at 10M capacity, 0.1% error rate).
