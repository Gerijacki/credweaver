
#[derive(Clone, Debug)]
pub struct CombinatorConfig {
    pub separators: Vec<String>,
    pub max_depth: usize,
    pub min_length: usize,
    pub max_length: usize,
}

impl Default for CombinatorConfig {
    fn default() -> Self {
        CombinatorConfig {
            separators: vec![
                String::new(),
                "_".to_string(),
                "-".to_string(),
                ".".to_string(),
                "|".to_string(),
            ],
            max_depth: 3,
            min_length: 6,
            max_length: 20,
        }
    }
}

/// State for iterating permutations at a given depth
struct PermutationState {
    depth: usize,
    indices: Vec<usize>,
    sep_index: usize,
    started: bool,
}

impl PermutationState {
    fn new(depth: usize) -> Self {
        PermutationState {
            depth,
            indices: (0..depth).collect(),
            sep_index: 0,
            started: false,
        }
    }
}

pub struct Combinator {
    tokens: Vec<String>,
    config: CombinatorConfig,
    current_depth: usize,
    perm_state: PermutationState,
    factoriadic: Vec<usize>,
    perm_count: usize,
    perm_index: usize,
    sep_index: usize,
}

impl Combinator {
    pub fn new(tokens: Vec<String>, config: CombinatorConfig) -> Self {
        let depth = 1;
        let n = tokens.len();
        let perm_count = if n >= depth { permutation_count(n, depth) } else { 0 };
        Combinator {
            tokens,
            config,
            current_depth: depth,
            perm_state: PermutationState::new(depth),
            factoriadic: vec![],
            perm_count,
            perm_index: 0,
            sep_index: 0,
        }
    }

    pub fn next_combination(&mut self) -> Option<String> {
        let n = self.tokens.len();
        if n == 0 {
            return None;
        }

        loop {
            if self.current_depth > self.config.max_depth || self.current_depth > n {
                return None;
            }

            if self.perm_index >= self.perm_count {
                // move to next depth
                self.current_depth += 1;
                if self.current_depth > self.config.max_depth || self.current_depth > n {
                    return None;
                }
                self.perm_count = permutation_count(n, self.current_depth);
                self.perm_index = 0;
                self.sep_index = 0;
                continue;
            }

            // Get current permutation indices from perm_index
            let indices = nth_permutation(n, self.current_depth, self.perm_index);

            // Get sep
            let seps = &self.config.separators;
            let sep = &seps[self.sep_index];

            let parts: Vec<&str> = indices.iter().map(|&i| self.tokens[i].as_str()).collect();
            let candidate = parts.join(sep.as_str());

            // Advance sep_index or perm_index
            self.sep_index += 1;
            if self.sep_index >= seps.len() {
                self.sep_index = 0;
                self.perm_index += 1;
            }

            let len = candidate.len();
            if len >= self.config.min_length && len <= self.config.max_length {
                return Some(candidate);
            }
            // else: candidate out of length range, try next
        }
    }
}

impl Iterator for Combinator {
    type Item = String;

    fn next(&mut self) -> Option<Self::Item> {
        self.next_combination()
    }
}

/// Compute P(n, k) = n! / (n-k)!
fn permutation_count(n: usize, k: usize) -> usize {
    if k > n {
        return 0;
    }
    let mut result = 1usize;
    for i in 0..k {
        result = result.saturating_mul(n - i);
    }
    result
}

/// Get the nth permutation of k items chosen from n (0-indexed).
/// Returns indices into the token array.
fn nth_permutation(n: usize, k: usize, mut index: usize) -> Vec<usize> {
    let mut available: Vec<usize> = (0..n).collect();
    let mut result = Vec::with_capacity(k);

    for i in 0..k {
        let remaining = n - i;
        let p = permutation_count(remaining - 1, k - i - 1);
        let chosen_pos = if p == 0 { 0 } else { index / p };
        index %= if p == 0 { 1 } else { p };
        let chosen_pos = chosen_pos.min(available.len() - 1);
        result.push(available.remove(chosen_pos));
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_combinator_depth1() {
        let tokens = vec!["john".to_string(), "doe".to_string()];
        let config = CombinatorConfig {
            separators: vec![String::new()],
            max_depth: 1,
            min_length: 1,
            max_length: 20,
        };
        let results: Vec<String> = Combinator::new(tokens, config).collect();
        assert!(results.contains(&"john".to_string()));
        assert!(results.contains(&"doe".to_string()));
    }

    #[test]
    fn test_combinator_depth2() {
        let tokens = vec!["john".to_string(), "doe".to_string()];
        let config = CombinatorConfig {
            separators: vec![String::new(), "_".to_string()],
            max_depth: 2,
            min_length: 1,
            max_length: 20,
        };
        let results: Vec<String> = Combinator::new(tokens, config).collect();
        assert!(results.contains(&"johndoe".to_string()));
        assert!(results.contains(&"doejohn".to_string()));
        assert!(results.contains(&"john_doe".to_string()));
    }

    #[test]
    fn test_nth_permutation() {
        let p = nth_permutation(3, 2, 0);
        assert_eq!(p.len(), 2);
    }
}
