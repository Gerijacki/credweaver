# Performance Analysis

## Benchmark Methodology

Benchmarks are run using the `benchmark` CLI command or the pytest benchmark
suite in `tests/benchmarks/bench_generation.py`.

Standard benchmark profile:

```yaml
name: john
surname: doe
nickname: johnny
birthdate: { day: 15, month: 6, year: 1990 }
pet_name: rex
company: acme
keywords: [test, secure]
```

This produces approximately 18 base tokens after `extract_with_variations`,
leading to millions of candidates after full mutation expansion.

## Typical Results

### Python-only pipeline (max_depth=3, leet_level=2, append 0-99)

| Stage | Throughput |
|-------|-----------|
| Strategy generation | ~2M candidates/s |
| After mutations | ~800K pass/s |
| After length filter | ~750K pass/s |
| After bloom dedup | ~600K pass/s |

### Python + Rust engine (same config)

| Stage | Throughput |
|-------|-----------|
| `generate_combinations` (Rust) | ~8-15M pass/s |
| Python output consumer | ~5-10M pass/s |

Speedup: **5-15x** depending on hardware, config, and token count.

## Scaling Characteristics

### With token count (depth=2)

| Tokens | Combinations | Python time | Rust time |
|--------|-------------|-------------|-----------|
| 5 | 20 | <1ms | <1ms |
| 10 | 90 | <1ms | <1ms |
| 20 | 380 | 2ms | <1ms |
| 50 | 2450 | 12ms | 2ms |
| 100 | 9900 | 50ms | 8ms |

### With depth (10 tokens, 4 separators)

| Depth | Combinations | Mutations (approx) | Python time | Rust time |
|-------|-------------|-------------------|-------------|-----------|
| 1 | 10 | 1,200 | <1ms | <1ms |
| 2 | 90 | 10,800 | 5ms | 1ms |
| 3 | 720 | 86,400 | 40ms | 7ms |
| 4 | 5040 | 604,800 | 280ms | 50ms |
| 5 | 30240 | 3,628,800 | 1700ms | 300ms |

### With mutation expansion

Each base candidate produces this many mutations at default settings:

- Case modes × leet variants × append variants
- 3 case modes × 2 leet variants × (1 + 100 numbers + 6 symbols + 56 years) × 2 prepend
  = 3 × 2 × 164 ≈ **984 mutations per base**

With `--preset aggressive` (leet_level=3, numbers 0-9999):
- ~3 × 2^7 × 10002 ≈ **3.8M mutations per base** (leet_level=3 is exponential)

Use `--preset aggressive` only with a small token set or very large storage.

## Memory Usage

| Component | Memory |
|-----------|--------|
| Python generator stack | ~50KB |
| Rust PasswordIterator | ~2KB |
| Bloom filter (10M, 0.1%) | ~17MB |
| Python BloomFilter (10M, 0.1%) | ~17MB |
| Output buffer (1MB write buffer) | 1MB |
| **Total typical** | **~20MB** |

The design deliberately avoids accumulating output in memory. The bloom filter
is the dominant memory consumer.

To reduce memory at the cost of more false positives (fewer duplicates removed):

```yaml
filters:
  bloom_capacity: 1000000  # 1M capacity → ~1.7MB
  bloom_error_rate: 0.01   # 1% false positive rate
```

## I/O Performance

Writing to disk is the bottleneck for large runs:

| Storage | Write speed | CredWeaver throughput ceiling |
|---------|------------|-------------------------------|
| NVMe SSD | ~3 GB/s | ~300M pass/s (10 bytes avg) |
| SATA SSD | ~500 MB/s | ~50M pass/s |
| HDD | ~100 MB/s | ~10M pass/s |
| /dev/null | unlimited | CPU-limited |

The file writer uses a 1MB write buffer (`buffering=1<<20`) to batch syscalls.
Compressed output (`--compress`) reduces I/O but adds ~20% CPU overhead.

## Profiling Tips

### Find Python bottleneck

```bash
python -m cProfile -s cumulative -m credweaver.cli benchmark --iterations 100000 2>&1 | head -30
```

### Profile Rust code

```bash
# Build with debug symbols
RUSTFLAGS="-C force-frame-pointers=yes" maturin develop
# Then use perf/flamegraph
cargo flamegraph -- --test
```

### Memory profiling

```python
import tracemalloc
tracemalloc.start()
# ... run generation ...
snapshot = tracemalloc.take_snapshot()
for stat in snapshot.statistics("lineno")[:10]:
    print(stat)
```

## Tuning for Maximum Speed

1. **Use the Rust engine**: `use_rust_engine: true` (default)
2. **Lower leet level**: `leet_level: 1` cuts mutation count by ~4x vs level 2
3. **Reduce depth**: `max_depth: 2` is 5x faster than `max_depth: 3`
4. **Narrow number range**: `numbers_range: [0, 9]` instead of `[0, 99]`
5. **Disable dedup for fast counting**: `dedup: false`
6. **Write to fast storage or /dev/null for benchmarking**
7. **Set `parallel_threads`** to match CPU count for Rust parallel operations

## Tuning for Maximum Coverage

1. `--preset aggressive` enables all case modes, leet level 3, numbers 0-9999
2. Add `padding: true` for padding mutations
3. Increase `max_depth: 4` or `5` for deeper token combinations
4. Add custom keywords: everything the target might use
5. Include `required_charset` to null only produces qualifying passwords

## Large-Scale Run Estimates

| Config | Tokens | Estimated output | Disk space (avg 10B) | Time (Rust) |
|--------|--------|-----------------|----------------------|-------------|
| fast preset | 10 | ~500K | 5MB | <1s |
| default preset | 15 | ~50M | 500MB | 10s |
| aggressive preset | 15 | ~500M | 5GB | 100s |
| aggressive preset | 20 | ~5B | 50GB | 20min |

These are rough estimates. Actual output depends heavily on profile richness
and configured filter bounds.
