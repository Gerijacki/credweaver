use serde::Deserialize;
use crate::combinator::{Combinator, CombinatorConfig};
use crate::mutations::{MutationConfig, apply_all_mutations};
use crate::dedup::StreamDeduplicator;

#[derive(Clone, Debug, Deserialize)]
pub struct GeneratorConfig {
    pub separators: Vec<String>,
    pub max_depth: usize,
    pub min_length: usize,
    pub max_length: usize,
    pub leet_level: u8,
    pub case_modes: Vec<String>,
    pub append_numbers: bool,
    pub number_range: (u32, u32),
    pub append_symbols: Vec<String>,
    pub append_years: Vec<u32>,
    pub use_bloom: bool,
    pub bloom_capacity: usize,
}

impl Default for GeneratorConfig {
    fn default() -> Self {
        GeneratorConfig {
            separators: vec![
                String::new(),
                "_".to_string(),
                "-".to_string(),
                ".".to_string(),
            ],
            max_depth: 3,
            min_length: 6,
            max_length: 20,
            leet_level: 2,
            case_modes: vec!["lower".to_string(), "title".to_string(), "upper".to_string()],
            append_numbers: true,
            number_range: (0, 99),
            append_symbols: vec!["!".to_string(), "@".to_string(), "#".to_string()],
            append_years: vec![],
            use_bloom: true,
            bloom_capacity: 10_000_000,
        }
    }
}

/// PasswordGenerator orchestrates combination, mutation, and deduplication.
pub struct PasswordGenerator {
    tokens: Vec<String>,
    config: GeneratorConfig,
}

impl PasswordGenerator {
    pub fn new(tokens: Vec<String>, config: GeneratorConfig) -> Self {
        PasswordGenerator { tokens, config }
    }

    /// Convert into a lazy iterator of generated passwords.
    pub fn into_iter(self) -> PasswordIterator {
        let combinator_config = CombinatorConfig {
            separators: self.config.separators.clone(),
            max_depth: self.config.max_depth,
            min_length: 1, // We filter later after mutations
            max_length: self.config.max_length,
        };
        let combinator = Combinator::new(self.tokens.clone(), combinator_config);

        let mutation_config = MutationConfig {
            leet_level: self.config.leet_level,
            case_modes: self.config.case_modes.clone(),
            append_numbers: self.config.append_numbers,
            number_range: self.config.number_range,
            append_symbols: self.config.append_symbols.clone(),
            append_years: self.config.append_years.clone(),
        };

        let dedup = if self.config.use_bloom {
            Some(StreamDeduplicator::new(self.config.bloom_capacity, 0.001))
        } else {
            None
        };

        PasswordIterator {
            combinator,
            mutation_config,
            min_length: self.config.min_length,
            max_length: self.config.max_length,
            pending: Vec::new(),
            pending_index: 0,
            dedup,
        }
    }
}

/// Lazy iterator that combines Combinator + Mutations + optional Dedup.
pub struct PasswordIterator {
    combinator: Combinator,
    mutation_config: MutationConfig,
    min_length: usize,
    max_length: usize,
    pending: Vec<String>,
    pending_index: usize,
    dedup: Option<StreamDeduplicator>,
}

impl Iterator for PasswordIterator {
    type Item = String;

    fn next(&mut self) -> Option<Self::Item> {
        loop {
            // Drain pending mutations first
            while self.pending_index < self.pending.len() {
                let candidate = self.pending[self.pending_index].clone();
                self.pending_index += 1;

                let len = candidate.len();
                if len < self.min_length || len > self.max_length {
                    continue;
                }

                if let Some(ref mut dedup) = self.dedup {
                    if !dedup.check_and_insert(&candidate) {
                        return Some(candidate);
                    }
                    // duplicate, continue
                } else {
                    return Some(candidate);
                }
            }

            // Get next base combination from combinator
            let base = self.combinator.next()?;

            // Apply all mutations to the base
            self.pending = apply_all_mutations(&base, &self.mutation_config);
            self.pending_index = 0;
        }
    }
}

/// Convenience function: generate a stream from tokens and config.
pub fn generate_stream(tokens: Vec<String>, config: GeneratorConfig) -> PasswordIterator {
    PasswordGenerator::new(tokens, config).into_iter()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_generator_basic() {
        let tokens = vec!["john".to_string(), "doe".to_string()];
        let config = GeneratorConfig {
            max_depth: 2,
            min_length: 4,
            max_length: 20,
            leet_level: 1,
            append_numbers: false,
            append_symbols: vec![],
            append_years: vec![],
            use_bloom: false,
            bloom_capacity: 1000,
            ..Default::default()
        };
        let results: Vec<String> = generate_stream(tokens, config).take(50).collect();
        assert!(!results.is_empty());
        for r in &results {
            assert!(r.len() >= 4 && r.len() <= 20);
        }
    }

    #[test]
    fn test_generator_with_dedup() {
        let tokens = vec!["test".to_string(), "pass".to_string()];
        let config = GeneratorConfig {
            max_depth: 1,
            min_length: 4,
            max_length: 20,
            leet_level: 0,
            append_numbers: false,
            append_symbols: vec![],
            append_years: vec![],
            use_bloom: true,
            bloom_capacity: 10_000,
            case_modes: vec!["lower".to_string()],
            ..Default::default()
        };
        let results: Vec<String> = generate_stream(tokens, config).collect();
        // With bloom dedup, we shouldn't see exact duplicates (with high probability)
        assert!(!results.is_empty());
    }
}
