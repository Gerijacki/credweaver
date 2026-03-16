use pyo3::prelude::*;
use pyo3::types::PyDict;

mod combinator;
mod mutations;
mod dedup;
mod entropy;
mod markov;
mod generator;

use mutations::{MutationConfig, apply_all_mutations};
use dedup::dedup_exact;
use entropy::{shannon_entropy, batch_score};
use markov::markov_generate;
use generator::{GeneratorConfig, PasswordIterator, generate_stream};

// ─── Helper: parse GeneratorConfig from a Python dict ────────────────────────

fn parse_generator_config(config: &Bound<'_, PyDict>) -> PyResult<GeneratorConfig> {
    let mut cfg = GeneratorConfig::default();

    if let Some(v) = config.get_item("separators")? {
        cfg.separators = v.extract::<Vec<String>>()?;
    }
    if let Some(v) = config.get_item("max_depth")? {
        cfg.max_depth = v.extract::<usize>()?;
    }
    if let Some(v) = config.get_item("min_length")? {
        cfg.min_length = v.extract::<usize>()?;
    }
    if let Some(v) = config.get_item("max_length")? {
        cfg.max_length = v.extract::<usize>()?;
    }
    if let Some(v) = config.get_item("leet_level")? {
        cfg.leet_level = v.extract::<u8>()?;
    }
    if let Some(v) = config.get_item("case_modes")? {
        cfg.case_modes = v.extract::<Vec<String>>()?;
    }
    if let Some(v) = config.get_item("append_numbers")? {
        cfg.append_numbers = v.extract::<bool>()?;
    }
    if let Some(v) = config.get_item("number_range")? {
        let range = v.extract::<Vec<u32>>()?;
        if range.len() >= 2 {
            cfg.number_range = (range[0], range[1]);
        }
    }
    if let Some(v) = config.get_item("append_symbols")? {
        cfg.append_symbols = v.extract::<Vec<String>>()?;
    }
    if let Some(v) = config.get_item("append_years")? {
        cfg.append_years = v.extract::<Vec<u32>>()?;
    }
    if let Some(v) = config.get_item("use_bloom")? {
        cfg.use_bloom = v.extract::<bool>()?;
    }
    if let Some(v) = config.get_item("bloom_capacity")? {
        cfg.bloom_capacity = v.extract::<usize>()?;
    }

    Ok(cfg)
}

// ─── CombinationIterator ──────────────────────────────────────────────────────

/// Python-iterable class that lazily yields password combinations.
#[pyclass]
pub struct CombinationIterator {
    inner: PasswordIterator,
}

#[pymethods]
impl CombinationIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<'_, Self>) -> Option<String> {
        slf.inner.next()
    }

    /// Collect up to `n` items into a Python list in a single FFI call.
    /// Much faster than calling __next__ n times.
    fn collect_batch(&mut self, n: usize) -> Vec<String> {
        let mut batch = Vec::with_capacity(n);
        for _ in 0..n {
            match self.inner.next() {
                Some(item) => batch.push(item),
                None => break,
            }
        }
        batch
    }

    /// Collect ALL remaining items. Use with caution on large sets.
    fn collect_all(&mut self) -> Vec<String> {
        self.inner.by_ref().collect()
    }
}

// ─── MutationIterator ─────────────────────────────────────────────────────────

/// Python-iterable class that lazily yields mutated passwords.
#[pyclass]
pub struct MutationIterator {
    passwords: Vec<String>,
    index: usize,
    pending: Vec<String>,
    pending_index: usize,
    config: MutationConfig,
    min_length: usize,
    max_length: usize,
}

#[pymethods]
impl MutationIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<'_, Self>) -> PyResult<Option<String>> {
        loop {
            // Drain pending mutations
            while slf.pending_index < slf.pending.len() {
                let candidate = slf.pending[slf.pending_index].clone();
                slf.pending_index += 1;
                let len = candidate.len();
                if len >= slf.min_length && len <= slf.max_length {
                    return Ok(Some(candidate));
                }
            }

            // Get next base password
            if slf.index >= slf.passwords.len() {
                return Ok(None);
            }

            let base = slf.passwords[slf.index].clone();
            slf.index += 1;

            let config = slf.config.clone();
            slf.pending = apply_all_mutations(&base, &config);
            slf.pending_index = 0;
        }
    }
}

// ─── Module-level functions ───────────────────────────────────────────────────

/// Generate password combinations from tokens using the Rust engine.
/// Returns a CombinationIterator (Python iterable).
#[pyfunction]
fn generate_combinations(
    tokens: Vec<String>,
    config: &Bound<'_, PyDict>,
) -> PyResult<CombinationIterator> {
    let cfg = parse_generator_config(config)?;
    let iter = generate_stream(tokens, cfg);
    Ok(CombinationIterator { inner: iter })
}

/// Apply mutations to a list of passwords.
/// Returns a MutationIterator (Python iterable).
#[pyfunction]
fn apply_mutations(
    passwords: Vec<String>,
    config: &Bound<'_, PyDict>,
) -> PyResult<MutationIterator> {
    let mut mut_config = MutationConfig::default();

    if let Some(v) = config.get_item("leet_level")? {
        mut_config.leet_level = v.extract::<u8>()?;
    }
    if let Some(v) = config.get_item("case_modes")? {
        mut_config.case_modes = v.extract::<Vec<String>>()?;
    }
    if let Some(v) = config.get_item("append_numbers")? {
        mut_config.append_numbers = v.extract::<bool>()?;
    }
    if let Some(v) = config.get_item("number_range")? {
        let range = v.extract::<Vec<u32>>()?;
        if range.len() >= 2 {
            mut_config.number_range = (range[0], range[1]);
        }
    }
    if let Some(v) = config.get_item("append_symbols")? {
        mut_config.append_symbols = v.extract::<Vec<String>>()?;
    }
    if let Some(v) = config.get_item("append_years")? {
        mut_config.append_years = v.extract::<Vec<u32>>()?;
    }

    let min_length = config
        .get_item("min_length")?
        .map(|v| v.extract::<usize>().unwrap_or(1))
        .unwrap_or(1);
    let max_length = config
        .get_item("max_length")?
        .map(|v| v.extract::<usize>().unwrap_or(100))
        .unwrap_or(100);

    Ok(MutationIterator {
        passwords,
        index: 0,
        pending: vec![],
        pending_index: 0,
        config: mut_config,
        min_length,
        max_length,
    })
}

/// Deduplicate a list of passwords using a HashSet. Returns unique passwords.
#[pyfunction]
fn deduplicate(passwords: Vec<String>) -> Vec<String> {
    dedup_exact(passwords)
}

/// Calculate Shannon entropy for a single password.
#[pyfunction]
fn entropy_score(password: &str) -> f64 {
    shannon_entropy(password)
}

/// Calculate Shannon entropy for a batch of passwords.
/// Returns list of (password, entropy) tuples.
#[pyfunction]
fn batch_entropy_score(passwords: Vec<String>) -> Vec<(String, f64)> {
    batch_score(passwords)
}

/// Generate passwords using a Markov chain trained on seed tokens.
#[pyfunction]
#[pyo3(name = "markov_generate")]
fn markov_generate_py(
    seed_tokens: Vec<String>,
    length: usize,
    count: usize,
) -> Vec<String> {
    markov_generate(seed_tokens, length, count)
}

// ─── Module definition ────────────────────────────────────────────────────────

#[pymodule]
fn cupp_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<CombinationIterator>()?;
    m.add_class::<MutationIterator>()?;
    m.add_function(wrap_pyfunction!(generate_combinations, m)?)?;
    m.add_function(wrap_pyfunction!(apply_mutations, m)?)?;
    m.add_function(wrap_pyfunction!(deduplicate, m)?)?;
    m.add_function(wrap_pyfunction!(entropy_score, m)?)?;
    m.add_function(wrap_pyfunction!(batch_entropy_score, m)?)?;
    m.add_function(wrap_pyfunction!(markov_generate_py, m)?)?;
    Ok(())
}
