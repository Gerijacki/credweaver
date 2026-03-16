# CredWeaver

> Weave profile data into targeted credential wordlists.

[![CI](https://github.com/Gerijacki/credweaver/actions/workflows/ci.yml/badge.svg)](https://github.com/Gerijacki/credweaver/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/rust-stable-orange.svg)](https://www.rust-lang.org/)
[![Security](https://img.shields.io/badge/use-authorized%20testing%20only-red.svg)](#ethical-use--legal)

**CredWeaver** is a fast, profile-driven credential wordlist generator built for authorized penetration testing, CTF competitions, and security research.

It takes personal information about a target (name, birth date, pet names, company, etc.) and **weaves** it into a tailored, high-quality password wordlist — far more effective than generic dictionaries.

Built as a modern Python + Rust hybrid, CredWeaver is a complete redesign of the classic [CUpp](https://github.com/Mebus/cupp) (Common User Passwords Profiler) tool, which has been largely unmaintained since 2021. CredWeaver keeps the core idea — profile-based generation — and rebuilds it with:

- Streaming pipeline (no RAM loading of full wordlist)
- Modular plugin architecture
- Pydantic v2 config and profile validation
- Rust engine (PyO3 + maturin) for compute-intensive paths
- Docker and Kubernetes support
- Full CI/CD, test suite, and type checking

---

## Features

- **Profile-driven generation** — name, surname, dates, pets, company, keywords
- **4 built-in strategies** — concatenation, date-based, keyboard patterns, common passwords
- **Layered mutations** — leet (3 levels), case (5 modes), append numbers/years/symbols
- **Streaming output** — generates millions of passwords without loading into RAM
- **Bloom filter dedup** — removes duplicates without a HashSet blowup
- **Rust engine** — multiplicative mutations via `credweaver_engine` (PyO3)
- **Config presets** — `fast`, `default`, `aggressive`
- **Multiple input formats** — interactive, YAML profile, JSON profile
- **Compressed output** — write `.txt` or `.gz` directly
- **Docker + Kubernetes** — production-ready deployment

---

## Quick Start

### Docker (zero install)
```bash
docker pull ghcr.io/Gerijacki/credweaver:latest
docker run --rm ghcr.io/Gerijacki/credweaver:latest --help
```

### pip
```bash
pip install credweaver
credweaver generate --interactive
```

### From source
```bash
git clone https://github.com/Gerijacki/credweaver
cd credweaver
python3 -m venv .venv && source .venv/bin/activate
pip install maturin pydantic pyyaml typer rich
maturin develop --release
credweaver --help
```

---

## Installation

### Requirements
- Python 3.11+
- Rust stable (only for building from source)

### From PyPI
```bash
pip install credweaver
```

### From source (with Rust engine)
```bash
git clone https://github.com/Gerijacki/credweaver
cd credweaver
python3 -m venv .venv && source .venv/bin/activate
pip install maturin pydantic pyyaml typer rich pytest
export PATH="$HOME/.cargo/bin:$PATH"
maturin develop --release
```

---

## Usage

### Interactive mode
```bash
credweaver generate --interactive
```

### From a profile file
```bash
credweaver generate --profile profiles/example_target.yaml --output wordlist.txt
```

### With a preset
```bash
credweaver generate --profile target.yaml --preset aggressive --output out.txt
```

### Enhance an existing wordlist
```bash
credweaver enhance --wordlist rockyou.txt --output enhanced.txt
```

### Generate a profile template
```bash
credweaver profile init --output target.yaml
# edit target.yaml, then:
credweaver generate --profile target.yaml
```

### Run benchmark
```bash
credweaver benchmark
```

### List strategies
```bash
credweaver strategies
```

---

## Profile Format

```yaml
# target.yaml
name: "john"
surname: "doe"
nickname: "johnny"
birthdate:
  day: 15
  month: 6
  year: 1990
partner_name: "jane"
pet_name: "rex"
company: "acme"
keywords:
  - "security"
  - "hacker"
```

---

## Configuration

Override defaults with `--config credweaver.yaml`:

```yaml
generation:
  max_depth: 3          # token combination depth
  separators: ["", "_", "-", "."]
  use_rust_engine: true

mutations:
  leet:
    enabled: true
    level: 2            # 1=basic, 2=medium, 3=all combos
  case:
    modes: [lower, title, upper]
  append:
    numbers: true
    numbers_range: [0, 99]
    symbols: ["!", "@", "123"]
    years: true
    years_range: [1970, 2025]

filters:
  min_length: 6
  max_length: 20
  dedup: true
```

---

## Architecture

```
Profile (YAML/JSON/interactive)
    ↓
Token Extractor (name variations, dates, keywords)
    ↓
Strategy Engine ──────────────────────────────────
  [Concatenation] [DateBased] [Keyboard] [Common]
    ↓
Pipeline ─────────────────────────────────────────
  Rust engine (credweaver_engine via PyO3)
    ↓ collect_batch(4096) — minimal FFI overhead
  OR Python fallback (automatic)
    ↓
Filters (length · charset · Bloom dedup)
    ↓
Streaming writer → .txt / .gz
```

**Rust engine** (`credweaver_engine`) handles the hot paths:
- Cartesian product combinator
- Multiplicative mutations (all combos of leet × case × append)
- Bloom filter deduplication
- Shannon entropy scoring
- Markov chain generation

→ See [docs/architecture.md](docs/architecture.md) for full details.

---

## Docker

```bash
# Build
docker build -t credweaver .

# Run against a profile
docker run --rm \
  -v $(pwd)/profiles:/home/credweaver/profiles:ro \
  -v $(pwd)/output:/output \
  credweaver generate \
    --profile /home/credweaver/profiles/example_target.yaml \
    --output /output/wordlist.txt

# Dev shell
docker compose up credweaver-dev
```

---

## Kubernetes

```bash
# Create namespace and deploy
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/job.yaml
```

See [k8s/README.md](k8s/README.md) for full deployment guide.

---

## Development

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
maturin develop --release

# Tests
pytest tests/unit/ tests/integration/ -v

# Lint + format
ruff check credweaver/ tests/
ruff format credweaver/ tests/
mypy credweaver/

# Rebuild Rust engine after .rs changes
maturin develop --release
```

### Git Hooks (pre-commit & pre-push)

CredWeaver uses [pre-commit](https://pre-commit.com/) for automated quality gates. Run **once** after cloning:

```bash
bash scripts/install-hooks.sh
```

This installs two hooks:

| Hook | Trigger | Checks |
|------|---------|--------|
| **pre-commit** | `git commit` | ruff lint, ruff format, mypy, cargo fmt, cargo clippy |
| **pre-push** | `git push` | full pytest suite, cargo test |

**Manual run** (without committing):
```bash
pre-commit run --all-files   # all pre-commit checks
```

**Emergency bypass** (use sparingly — CI will still catch failures):
```bash
git commit --no-verify
git push   --no-verify
```

The pre-commit hook configuration lives in `.pre-commit-config.yaml`. The pre-push hook script is at `scripts/pre-push`.

### Adding a new strategy (plugin)
```python
# credweaver/strategies/my_strategy.py
from credweaver.strategies.base import Strategy
from credweaver.strategies.registry import register

@register("my_strategy")
class MyStrategy(Strategy):
    description = "My custom strategy"

    def generate(self, profile):
        yield f"{profile.name}custom"
```

---

## Origin

CredWeaver is inspired by **[CUpp](https://github.com/Mebus/cupp)** (Common User Passwords Profiler), originally written by Mebus. CUpp pioneered the idea of profile-driven password generation but has been largely unmaintained since 2021.

CredWeaver is a **ground-up redesign** that keeps the core concept and adds:
- Streaming (no RAM blowup)
- Plugin system
- Rust engine
- Modern Python tooling (Pydantic v2, Typer, ruff)
- Docker/K8s deployment
- Full test suite and CI/CD

CUpp remains the original inspiration and reference implementation.

---

## Ethical Use & Legal

CredWeaver is intended **exclusively** for:

- Authorized penetration testing
- Security audits with **written permission**
- CTF competitions
- Security research and education

**Using this tool against systems you do not own or have explicit written authorization to test is illegal and unethical.**

The authors accept no liability for misuse.

---

## Contributing

1. Fork and clone
2. Set up the dev environment (see Development above)
3. Install git hooks: `bash scripts/install-hooks.sh`
4. Create a branch: `git checkout -b feat/my-feature`
5. Make changes and add tests — hooks enforce quality automatically
6. Open a pull request

---

## License

MIT — see [LICENSE](LICENSE).
