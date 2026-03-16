use rayon::prelude::*;
use std::collections::HashMap;

/// Calculate Shannon entropy of a string.
/// H = -sum(p * log2(p)) for each unique character frequency.
pub fn shannon_entropy(s: &str) -> f64 {
    if s.is_empty() {
        return 0.0;
    }

    let len = s.chars().count() as f64;
    let mut freq: HashMap<char, usize> = HashMap::new();
    for ch in s.chars() {
        *freq.entry(ch).or_insert(0) += 1;
    }

    let entropy = freq.values().fold(0.0f64, |acc, &count| {
        let p = count as f64 / len;
        acc - p * p.log2()
    });

    entropy
}

/// Estimate bits of entropy based on charset size: log2(charset_size) * length.
pub fn charset_entropy(s: &str) -> f64 {
    if s.is_empty() {
        return 0.0;
    }

    let mut has_lower = false;
    let mut has_upper = false;
    let mut has_digit = false;
    let mut has_symbol = false;

    for ch in s.chars() {
        if ch.is_ascii_lowercase() {
            has_lower = true;
        } else if ch.is_ascii_uppercase() {
            has_upper = true;
        } else if ch.is_ascii_digit() {
            has_digit = true;
        } else {
            has_symbol = true;
        }
    }

    let mut charset_size = 0usize;
    if has_lower {
        charset_size += 26;
    }
    if has_upper {
        charset_size += 26;
    }
    if has_digit {
        charset_size += 10;
    }
    if has_symbol {
        charset_size += 33;
    }

    if charset_size == 0 {
        return 0.0;
    }

    let length = s.len() as f64;
    (charset_size as f64).log2() * length
}

/// Combined strength score normalized to 0.0-1.0.
/// score = (shannon_entropy * 0.6 + charset_bits_normalized * 0.4)
pub fn strength_score(s: &str) -> f64 {
    if s.is_empty() {
        return 0.0;
    }

    let shannon = shannon_entropy(s);
    let charset = charset_entropy(s);

    // Normalize: max Shannon entropy for typical passwords ~4.0 bits/char,
    // max charset entropy for 20-char password with full charset ~131 bits.
    // We normalize to reasonable maximums.
    let max_shannon = 4.0 * s.len() as f64;
    let max_charset = 6.5 * 20.0; // log2(95) * 20

    let normalized_shannon = if max_shannon > 0.0 {
        (shannon / max_shannon).min(1.0)
    } else {
        0.0
    };

    let normalized_charset = if max_charset > 0.0 {
        (charset / max_charset).min(1.0)
    } else {
        0.0
    };

    (normalized_shannon * 0.6 + normalized_charset * 0.4).min(1.0)
}

/// Score a single password, returning (password, entropy).
pub fn score_password(password: &str) -> (String, f64) {
    (password.to_string(), shannon_entropy(password))
}

/// Rank passwords by Shannon entropy in descending order, using rayon for parallel scoring.
pub fn rank_passwords_parallel(passwords: Vec<String>) -> Vec<(String, f64)> {
    let mut scored: Vec<(String, f64)> = passwords
        .into_par_iter()
        .map(|p| {
            let entropy = shannon_entropy(&p);
            (p, entropy)
        })
        .collect();

    scored.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    scored
}

/// Score a batch of passwords, returning (password, entropy) pairs.
pub fn batch_score(passwords: Vec<String>) -> Vec<(String, f64)> {
    passwords
        .into_par_iter()
        .map(|p| {
            let score = shannon_entropy(&p);
            (p, score)
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_entropy_empty() {
        assert_eq!(shannon_entropy(""), 0.0);
    }

    #[test]
    fn test_entropy_uniform() {
        // "aaa" has entropy 0
        let e = shannon_entropy("aaa");
        assert!((e - 0.0).abs() < 1e-10);
    }

    #[test]
    fn test_entropy_varied() {
        // "ab" has entropy 1.0
        let e = shannon_entropy("ab");
        assert!((e - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_charset_entropy_lower_only() {
        let e = charset_entropy("hello");
        // log2(26) * 5 ≈ 4.7 * 5 ≈ 23.5
        assert!(e > 20.0 && e < 30.0);
    }

    #[test]
    fn test_strength_score_range() {
        let s = strength_score("P@ssw0rd!");
        assert!(s >= 0.0 && s <= 1.0);
    }

    #[test]
    fn test_rank_passwords() {
        let passwords = vec![
            "aaa".to_string(),
            "P@ssw0rd!".to_string(),
            "abc".to_string(),
        ];
        let ranked = rank_passwords_parallel(passwords);
        // "P@ssw0rd!" should have higher entropy than "aaa"
        assert!(ranked[0].1 >= ranked[ranked.len() - 1].1);
    }
}
