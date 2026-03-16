use rayon::prelude::*;
use std::collections::HashMap;

/// Simple Markov chain for password generation.
/// Transitions are stored as: state -> (next_char_or_token, count)
pub struct MarkovChain {
    pub transitions: HashMap<String, HashMap<String, u32>>,
    pub order: usize,
}

impl MarkovChain {
    pub fn new() -> Self {
        MarkovChain {
            transitions: HashMap::new(),
            order: 2,
        }
    }

    /// Train the Markov chain from a list of seed tokens (character-level bigrams).
    pub fn train(&mut self, tokens: &[String], order: usize) {
        self.order = order;
        for token in tokens {
            let chars: Vec<char> = token.chars().collect();
            if chars.len() < order + 1 {
                // For short tokens, use the whole token as a transition
                let entry = self.transitions.entry(token.clone()).or_default();
                *entry.entry(token.clone()).or_insert(0) += 1;
                continue;
            }
            for i in 0..=(chars.len().saturating_sub(order + 1)) {
                let state: String = chars[i..i + order].iter().collect();
                let next: String = chars[i + order..i + order + 1].iter().collect();
                let entry = self.transitions.entry(state).or_default();
                *entry.entry(next).or_insert(0) += 1;
            }
        }
    }

    /// Generate a sequence starting from `start`, up to `max_len` characters.
    /// Uses a deterministic LCG seeded with `rng_seed`.
    pub fn generate(&self, start: &str, max_len: usize, rng_seed: u64) -> String {
        if self.transitions.is_empty() {
            return start.to_string();
        }

        let mut result = String::new();
        let start_chars: Vec<char> = start.chars().collect();

        // Seed enough characters
        let mut window: Vec<char> = if start_chars.len() >= self.order {
            start_chars[..self.order].to_vec()
        } else {
            start_chars.clone()
        };
        result.extend(window.iter());

        let mut rng = LcgRng::new(rng_seed);

        while result.len() < max_len {
            let state: String = window.iter().collect();
            let next_chars = match self.transitions.get(&state) {
                Some(m) => m,
                None => break,
            };

            // Pick a weighted random next character
            let total: u32 = next_chars.values().sum();
            if total == 0 {
                break;
            }

            let mut target = rng.next_u32() % total;
            let mut chosen = None;
            for (ch, &count) in next_chars {
                if target < count {
                    chosen = Some(ch.clone());
                    break;
                }
                target -= count;
            }

            match chosen {
                Some(next) => {
                    result.push_str(&next);
                    // Advance the window
                    for ch in next.chars() {
                        if window.len() >= self.order {
                            window.remove(0);
                        }
                        window.push(ch);
                    }
                }
                None => break,
            }
        }

        result.chars().take(max_len).collect()
    }

    /// Generate multiple sequences in parallel using rayon.
    pub fn generate_batch_parallel(
        &self,
        seeds: &[String],
        count_per_seed: usize,
        max_len: usize,
    ) -> Vec<String> {
        let seeds_vec: Vec<String> = seeds.to_vec();
        seeds_vec
            .into_par_iter()
            .flat_map(|seed| {
                (0..count_per_seed)
                    .map(|i| {
                        // Use different seeds for variety
                        let rng_seed = fnv1a_simple(seed.as_bytes()).wrapping_add(i as u64);
                        self.generate(&seed, max_len, rng_seed)
                    })
                    .collect::<Vec<_>>()
            })
            .collect()
    }
}

impl Default for MarkovChain {
    fn default() -> Self {
        Self::new()
    }
}

/// Simple Linear Congruential Generator for deterministic randomness.
struct LcgRng {
    state: u64,
}

impl LcgRng {
    fn new(seed: u64) -> Self {
        LcgRng { state: seed | 1 }
    }

    fn next_u64(&mut self) -> u64 {
        self.state = self.state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        self.state
    }

    fn next_u32(&mut self) -> u32 {
        (self.next_u64() >> 32) as u32
    }
}

fn fnv1a_simple(data: &[u8]) -> u64 {
    let mut hash: u64 = 0xcbf29ce484222325;
    for &byte in data {
        hash ^= byte as u64;
        hash = hash.wrapping_mul(0x100000001b3);
    }
    hash
}

/// High-level function: train and generate passwords in one call.
pub fn markov_generate(
    seed_tokens: Vec<String>,
    length: usize,
    count: usize,
) -> Vec<String> {
    if seed_tokens.is_empty() || length == 0 || count == 0 {
        return vec![];
    }

    let mut chain = MarkovChain::new();
    chain.train(&seed_tokens, 2);

    let per_seed = (count / seed_tokens.len()).max(1);
    let mut results = chain.generate_batch_parallel(&seed_tokens, per_seed, length);

    // Trim to exactly `count` if we generated more
    results.truncate(count);

    // Fill up if we got fewer than `count`
    while results.len() < count {
        let seed = &seed_tokens[results.len() % seed_tokens.len()];
        let rng_seed = results.len() as u64 * 0x9e3779b97f4a7c15;
        results.push(chain.generate(seed, length, rng_seed));
    }

    results
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_train_and_generate() {
        let tokens = vec!["john".to_string(), "jane".to_string(), "johnny".to_string()];
        let mut chain = MarkovChain::new();
        chain.train(&tokens, 2);
        assert!(!chain.transitions.is_empty());
        let result = chain.generate("jo", 8, 42);
        assert!(!result.is_empty());
    }

    #[test]
    fn test_generate_batch() {
        let tokens = vec!["password".to_string(), "secure".to_string()];
        let mut chain = MarkovChain::new();
        chain.train(&tokens, 2);
        let results = chain.generate_batch_parallel(&tokens, 3, 8);
        assert_eq!(results.len(), 6);
    }

    #[test]
    fn test_markov_generate_function() {
        let seeds = vec!["john".to_string(), "doe".to_string(), "rex".to_string()];
        let results = markov_generate(seeds, 6, 5);
        assert!(!results.is_empty());
        for r in &results {
            assert!(!r.is_empty());
        }
    }

    #[test]
    fn test_lcg_rng() {
        let mut rng = LcgRng::new(12345);
        let a = rng.next_u64();
        let b = rng.next_u64();
        assert_ne!(a, b);
    }
}
