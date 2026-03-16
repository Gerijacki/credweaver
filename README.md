# CUPP v2 — Advanced Password Wordlist Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Rust](https://img.shields.io/badge/rust-stable-orange.svg)](https://www.rust-lang.org/)
[![PyO3](https://img.shields.io/badge/PyO3-0.21-blue.svg)](https://pyo3.rs/)

---

## About

CUPP v2 is a **Python + Rust hybrid** password wordlist generator for authorized penetration testing and security auditing. It generates highly targeted wordlists from personal profile information (names, dates, relationships, keywords) using a configurable pipeline of generation strategies and mutation rules.

This project is a modern implementation inspired by the original [CUpp (Common User Passwords Profiler)](https://github.com/Mebus/cupp) created by Mebus. The original CUpp introduced the practical idea of profile-driven password wordlist generation and has been widely used within the security community for many years.

CUPP v2 builds on that idea and explores how the same concept can be implemented with a more modular architecture and modern tooling. The goal is to make the approach easier to extend, test, and integrate into contemporary security workflows while preserving the spirit of the original project.

> **Legal notice**: This tool is intended for authorized security testing **only**.
> Always obtain explicit written permission before using it against any system, account, or service you do not own.

---

## Features

- **Profile-based generation**: names, dates, partners, children, pets, companies, phone numbers, keywords
- **Streaming pipeline**: constant memory usage regardless of output size — no full wordlist in RAM
- **Multiple strategies**: concatenation, date-based combinations, keyboard patterns, common passwords
- **Rust extension engine**: 5–15x speedup via PyO3/maturin for combinatorial and mutation-heavy workloads
- **Three mutation levels**: leet substitutions (3 levels), case variants (lower/upper/title/toggle/camel), number/symbol/year appending, padding
- **Bloom filter deduplication**: O(1) memory dedup using probabilistic bit arrays
- **Gzip output**: write compressed wordlists directly
- **Pydantic v2 validation**: all config and profile input is validated at the boundary
- **Extensible strategy plugin system**: add new generation strategies with one decorator
- **Rich CLI**: progress bars, stats table, benchmark comparisons
- **Full test suite**: unit, integration, and benchmark tests with coverage reporting
- **Docker + Kubernetes**: multi-stage Dockerfile, docker-compose dev environment, K8s Job/CronJob manifests
- **GitHub Actions CI/CD**: lint, test matrix, Rust tests, wheel builds, security scans, release automation

---

## Quick Start

### Docker (no install required)

```bash
# Generate from the bundled example profile
docker run --rm \
  -v $(pwd)/output:/output \
  ghcr.io/Gerijacki/cupp_v2:latest \
  generate \
    --profile /home/cupp/profiles/example_target.yaml \
    --output /output/wordlist.txt

# Interactive mode
docker run --rm -it \
  -v $(pwd)/output:/output \
  ghcr.io/Gerijacki/cupp_v2:latest \
  generate --interactive --output /output/wordlist.txt
```

### Local install

```bash
git clone https://github.com/Gerijacki/cupp_v2
cd cupp_v2
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
maturin develop --release   # build Rust engine (optional but recommended)
cupp --help
```

---

## Installation

### Requirements

- Python 3.11 or later
- Rust stable toolchain (for the Rust engine; the tool falls back to pure Python if Rust is absent)

### From source (recommended for development)

```bash
git clone https://github.com/Gerijacki/cupp_v2
cd cupp_v2

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate           # Windows

# Install Python dependencies (including dev extras)
pip install -e ".[dev]"

# Build and install the Rust engine (requires Rust stable)
pip install maturin
maturin develop --release

# Verify everything works
cupp --help
python3 -m pytest tests/unit/ tests/integration/ -v
```

### Without Rust

Skipping the `maturin develop` step is supported. CUPP v2 falls back to the pure Python pipeline automatically. You will see `Rust engine: OFF (Python fallback)` in the CLI output. Expect ~5–15x lower throughput on deep generation runs.

### From wheel (after a release)

```bash
pip install cupp-v2        # when published to PyPI
# or install a wheel from the GitHub Releases page:
pip install cupp_v2-2.0.0-cp312-cp312-manylinux_2_17_x86_64.whl
```

---

## Usage

### Generate a wordlist from a profile file

```bash
# Initialize a blank profile template
cupp profile init --output target.yaml

# Edit target.yaml with known information about the target, then:
cupp generate --profile target.yaml --output wordlist.txt
```

### Interactive mode

```bash
cupp generate --interactive --output wordlist.txt
```

### Use a preset

```bash
# fast: depth 2, leet level 1, numbers 0-9
cupp generate --profile target.yaml --preset fast

# aggressive: depth 4, leet level 3, numbers 0-9999, all case modes, padding
cupp generate --profile target.yaml --preset aggressive --output big.txt
```

### Dry run (count without writing)

```bash
cupp generate --profile target.yaml --dry-run
```

### Gzip output

```bash
cupp generate --profile target.yaml -o wordlist.txt --compress
# writes wordlist.txt.gz
```

### Enhance an existing wordlist

```bash
cupp enhance rockyou.txt --output rockyou_enhanced.txt
cupp enhance rockyou.txt --preset aggressive -o rockyou_aggressive.txt
```

### Run the benchmark

```bash
cupp benchmark
cupp benchmark --iterations 500000
```

### List available strategies

```bash
cupp strategies list
```

### Validate a config file

```bash
cupp config validate --config my_cupp.yaml
```

### Python API

```python
from cupp import Engine, Profile
from cupp.core.profile import DateInfo

profile = Profile(
    name="john",
    surname="doe",
    nickname="johnny",
    birthdate=DateInfo(day=15, month=6, year=1990),
    pet_name="rex",
    company="acme",
    keywords=["security", "hacker"],
)

engine = Engine()

# Lazy streaming iterator — no memory accumulation
for password in engine.generate(profile):
    print(password)

# Write directly to file
from pathlib import Path
stats = engine.generate_to_file(profile, Path("wordlist.txt"))
print(f"Generated {stats.total_generated:,} passwords in {stats.elapsed_seconds:.2f}s")
```

### Custom config via Python API

```python
from cupp import Engine, Profile
from cupp.config.loader import load_config, merge_config

cfg = load_config()
cfg = merge_config(cfg, {
    "generation": {"max_depth": 2},
    "mutations": {
        "leet": {"level": 1},
        "append": {"numbers_range": [0, 9], "years": False},
    },
    "filters": {"min_length": 8, "max_length": 16},
})

engine = Engine(config=cfg)
```

---

## Profile Format

Profiles are YAML (or JSON) files. All fields are optional — the more you provide, the more targeted the output.

```yaml
name: "john"
surname: "doe"
nickname: "johnny"
birthdate:
  day: 15
  month: 6
  year: 1990

partner_name: "jane"
partner_nickname: "janey"
partner_birthdate:
  day: 3
  month: 11
  year: 1992

child_name: "emma"
child_nickname: "emmy"
child_birthdate:
  day: 20
  month: 8
  year: 2015

pet_name: "rex"
company: "acme"
phone: "555-1234"

keywords:
  - "security"
  - "hacker"
```

---

## Configuration

Default config is embedded in the package and also available as `cupp.yaml` in the project root. Override with `--config path/to/config.yaml`.

```yaml
generation:
  max_depth: 3 # combination depth: 1=single tokens, 2=pairs, 3=triples
  separators: ["", "_", "-", "."]
  use_rust_engine: true
  parallel_threads: null # null = auto

mutations:
  leet:
    enabled: true
    level: 2 # 1=basic (e→3, a→@), 2=extended, 3=all combos (exponential)
  case:
    modes: [lower, title, upper] # also: toggle, camel
  append:
    numbers: true
    numbers_range: [0, 99]
    symbols: ["!", "@", "#", "123", "1234", "!@#"]
    years: true
    years_range: [1970, 2025]
  padding: false # true = wrap with !, ##, etc.

filters:
  min_length: 6
  max_length: 20
  dedup: true
  bloom_capacity: 10000000 # max unique passwords tracked by bloom filter
  bloom_error_rate: 0.001 # 0.1% false positive rate
  required_charset: null # e.g. ["upper", "digit"] to enforce complexity

strategies:
  enabled:
    - concatenation
    - date_based
    - keyboard_patterns
    - common_passwords
```

---

## Architecture

CUPP v2 uses a layered streaming pipeline:

```
Profile Input → TokenExtractor → Strategies → Rust/Python Mutations → Filters → Output
```

The Rust engine (`cupp_engine`, compiled via maturin/PyO3) handles combinatorial generation and multiplicative mutations. It is optional — the pure Python fallback pipeline is always available. The critical performance technique is `collect_batch(4096)`: a single FFI crossing that retrieves 4096 passwords at once, reducing FFI overhead by 4096x compared to per-password `__next__` calls.

For the full architecture document including the detailed data flow diagram, module map, Python↔Rust integration details, and performance analysis, see [docs/architecture.md](docs/architecture.md).

See also:

- [docs/rust_engine.md](docs/rust_engine.md) — Rust engine API reference
- [docs/plugin_system.md](docs/plugin_system.md) — Writing custom strategies
- [docs/performance.md](docs/performance.md) — Performance analysis and tuning guide

---

## Development

### Setup

```bash
git clone https://github.com/Gerijacki/cupp_v2
cd cupp_v2
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
maturin develop --release
```

### Running tests

```bash
# All tests (unit + integration)
pytest tests/unit/ tests/integration/ -v

# With coverage
pytest tests/ -v --cov=cupp --cov-report=html --cov-report=term-missing

# Benchmarks (verbose output, longer runtime)
pytest tests/benchmarks/ -v -s

# Rust engine integration tests (requires compiled engine)
pytest tests/integration/test_rust_engine.py -v
```

### Lint and type checking

```bash
ruff check cupp/ tests/
ruff format cupp/ tests/
mypy cupp/
```

### After changing Rust source

```bash
maturin develop --release
```

### Adding a new strategy

1. Create `cupp/strategies/my_strategy.py`
2. Implement the strategy class with `@register("my_strategy")`
3. Import it in `cupp/strategies/__init__.py` or `cupp/cli.py`
4. Add `"my_strategy"` to `strategies.enabled` in your config

```python
from cupp.strategies.base import Strategy
from cupp.strategies.registry import register

@register("my_strategy")
class MyStrategy(Strategy):
    description = "My custom generation strategy"

    def generate(self, profile):
        for token in profile.to_tokens():
            yield f"{token}custom"
            yield f"custom{token}"
```

---

## Docker & Kubernetes

### Docker

```bash
# Build
docker build -t cupp-v2 .

# Run against a profile
docker run --rm \
  -v $(pwd)/profiles:/home/cupp/profiles:ro \
  -v $(pwd)/output:/output \
  cupp-v2 generate \
    --profile /home/cupp/profiles/example_target.yaml \
    --output /output/wordlist.txt \
    --preset aggressive

# Development shell (with Rust toolchain, source mounted)
docker compose up cupp-dev

# Run test suite inside Docker
docker compose run cupp-test
```

### Kubernetes

The `k8s/` directory contains all manifests for running CUPP v2 as a Kubernetes Job or CronJob:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/configmap.yaml

# Create a profile ConfigMap
kubectl create configmap cupp-profiles \
  --from-file=target.yaml=profiles/example_target.yaml \
  --namespace cupp-v2

# Run a one-shot generation job
kubectl apply -f k8s/job.yaml
kubectl logs -n cupp-v2 -l component=generator -f

# Schedule nightly generation
kubectl apply -f k8s/cronjob.yaml
```

See [k8s/README.md](k8s/README.md) for the full deployment guide including how to retrieve output from the PVC and monitoring instructions.

---

## Ethical Use / Legal

CUPP v2 is a security research and penetration testing tool. It is provided for **lawful, authorized use only**.

**Permitted uses:**

- Authorized penetration testing engagements with written client permission
- Security audits where you own or have explicit written authorization for all target systems
- CTF (Capture The Flag) competitions
- Security research and education in controlled lab environments
- Testing your own accounts and systems

**Prohibited uses:**

- Attacking or accessing systems, accounts, or services without explicit written authorization
- Any use that violates applicable laws, including the Computer Fraud and Abuse Act (CFAA), the UK Computer Misuse Act, the EU Directive on Attacks Against Information Systems, or equivalent legislation in your jurisdiction
- Facilitating unauthorized access by a third party

The authors and contributors bear no responsibility for misuse of this software. By using CUPP v2, you agree that you are solely responsible for ensuring your use is lawful and authorized.

---

## Contributing

Contributions are welcome. Please:

1. Fork the repository and create a feature branch
2. Write tests for new functionality (unit tests in `tests/unit/`, integration tests in `tests/integration/`)
3. Ensure `ruff check`, `ruff format --check`, and `mypy cupp/` all pass
4. Ensure `pytest tests/unit/ tests/integration/` passes
5. If adding or modifying Rust code: run `cargo fmt` and `cargo clippy -- -D warnings`
6. Open a pull request against `main` with a clear description of the change

For bug reports and feature requests, open an issue on GitHub.

---

## License

MIT License. See [LICENSE](LICENSE) for the full text.

This project is an independent implementation inspired by the original CUpp project created by Mebus. It is not officially affiliated with the original project.
