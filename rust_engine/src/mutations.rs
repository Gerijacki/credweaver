use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct MutationConfig {
    pub leet_level: u8,
    pub case_modes: Vec<String>,
    pub append_numbers: bool,
    pub number_range: (u32, u32),
    pub append_symbols: Vec<String>,
    pub append_years: Vec<u32>,
}

impl Default for MutationConfig {
    fn default() -> Self {
        MutationConfig {
            leet_level: 2,
            case_modes: vec!["lower".to_string(), "title".to_string(), "upper".to_string()],
            append_numbers: true,
            number_range: (0, 99),
            append_symbols: vec!["!".to_string(), "@".to_string(), "#".to_string()],
            append_years: vec![],
        }
    }
}

fn leet_map(level: u8) -> HashMap<char, Vec<char>> {
    let mut map = HashMap::new();
    // Level 1
    map.insert('a', vec!['@']);
    map.insert('e', vec!['3']);
    map.insert('i', vec!['1']);
    map.insert('o', vec!['0']);
    map.insert('s', vec!['5']);

    if level >= 2 {
        map.entry('a').or_default().push('4');
        map.insert('t', vec!['7']);
        map.insert('g', vec!['9']);
        map.insert('b', vec!['8']);
    }

    if level >= 3 {
        map.insert('l', vec!['1']);
        map.insert('z', vec!['2']);
        map.insert('h', vec!['#']);
    }

    map
}

/// Apply leet substitutions at given level.
/// Level 1 & 2: single pass substitution (most common variant).
/// Level 3: generates ALL possible combinations (exponential).
pub fn apply_leet(s: &str, level: u8) -> Vec<String> {
    if level == 0 {
        return vec![s.to_string()];
    }

    let map = leet_map(level);
    let mut results = vec![s.to_string()];

    if level < 3 {
        // Single-pass: substitute first replacement only
        let mut variant = String::with_capacity(s.len());
        for ch in s.chars() {
            let lower = ch.to_lowercase().next().unwrap_or(ch);
            if let Some(replacements) = map.get(&lower) {
                variant.push(replacements[0]);
            } else {
                variant.push(ch);
            }
        }
        if variant != s {
            results.push(variant);
        }
    } else {
        // Level 3: all combinations
        let chars: Vec<char> = s.chars().collect();
        let mut combinations = all_leet_combos(&chars, &map);
        combinations.retain(|c| c != s);
        results.extend(combinations);
    }

    results
}

fn all_leet_combos(chars: &[char], map: &HashMap<char, Vec<char>>) -> Vec<String> {
    if chars.is_empty() {
        return vec![String::new()];
    }

    let ch = chars[0];
    let lower = ch.to_lowercase().next().unwrap_or(ch);
    let rest = all_leet_combos(&chars[1..], map);

    let mut variants = vec![ch];
    if let Some(replacements) = map.get(&lower) {
        variants.extend_from_slice(replacements);
    }

    let mut result = Vec::new();
    for v in &variants {
        for r in &rest {
            let mut s = String::new();
            s.push(*v);
            s.push_str(r);
            result.push(s);
        }
    }
    result
}

fn title_case(s: &str) -> String {
    let mut result = String::with_capacity(s.len());
    let mut capitalize_next = true;
    for ch in s.chars() {
        if ch.is_whitespace() {
            capitalize_next = true;
            result.push(ch);
        } else if capitalize_next {
            for c in ch.to_uppercase() {
                result.push(c);
            }
            capitalize_next = false;
        } else {
            result.push(ch);
        }
    }
    result
}

fn toggle_case(s: &str) -> String {
    s.chars()
        .enumerate()
        .map(|(i, c)| {
            if i % 2 == 0 {
                c.to_uppercase().next().unwrap_or(c)
            } else {
                c.to_lowercase().next().unwrap_or(c)
            }
        })
        .collect()
}

fn camel_case(s: &str) -> String {
    if s.is_empty() {
        return String::new();
    }
    let mut result = String::with_capacity(s.len());
    let mut chars = s.chars();
    if let Some(first) = chars.next() {
        for c in first.to_lowercase() {
            result.push(c);
        }
    }
    let rest: String = chars.collect();
    let titled = title_case(&rest);
    result.push_str(&titled);
    result
}

/// Apply case mutations according to mode strings.
pub fn apply_case(s: &str, modes: &[String]) -> Vec<String> {
    let mut results = Vec::new();
    let mut seen = std::collections::HashSet::new();

    // Always include original
    seen.insert(s.to_string());
    results.push(s.to_string());

    for mode in modes {
        let variant = match mode.as_str() {
            "lower" => s.to_lowercase(),
            "upper" => s.to_uppercase(),
            "title" => title_case(s),
            "toggle" => toggle_case(s),
            "camel" => camel_case(s),
            _ => continue,
        };
        if seen.insert(variant.clone()) {
            results.push(variant);
        }
    }
    results
}

/// Apply number, symbol, and year appending mutations.
pub fn apply_append(
    s: &str,
    numbers: bool,
    num_range: (u32, u32),
    symbols: &[String],
    years: &[u32],
) -> Vec<String> {
    let mut results = vec![s.to_string()];

    if numbers {
        let (lo, hi) = num_range;
        for n in lo..=hi {
            results.push(format!("{}{}", s, n));
            if n > 0 {
                results.push(format!("{}{}", n, s));
            }
        }
    }

    for sym in symbols {
        results.push(format!("{}{}", s, sym));
        results.push(format!("{}{}", sym, s));
    }

    for &year in years {
        results.push(format!("{}{}", s, year));
        let y2 = year % 100;
        results.push(format!("{}{:02}", s, y2));
    }

    results
}

/// Apply all configured mutations to a single word.
pub fn apply_all_mutations(word: &str, config: &MutationConfig) -> Vec<String> {
    let mut results = Vec::new();

    // Case variants first
    let case_variants = apply_case(word, &config.case_modes);

    for variant in &case_variants {
        // Leet variants of each case variant
        let leet_variants = apply_leet(variant, config.leet_level);

        for leet in &leet_variants {
            // Append mutations
            let appended = apply_append(
                leet,
                config.append_numbers,
                config.number_range,
                &config.append_symbols,
                &config.append_years,
            );
            results.extend(appended);
        }
    }

    results
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_leet_level1() {
        let results = apply_leet("password", 1);
        assert!(results.contains(&"password".to_string()));
        assert!(results.iter().any(|r| r.contains('0') || r.contains('@')));
    }

    #[test]
    fn test_case_upper() {
        let results = apply_case("hello", &["upper".to_string()]);
        assert!(results.contains(&"HELLO".to_string()));
    }

    #[test]
    fn test_case_title() {
        let results = apply_case("hello world", &["title".to_string()]);
        assert!(results.contains(&"Hello World".to_string()));
    }

    #[test]
    fn test_append_numbers() {
        let results = apply_append("test", true, (0, 3), &[], &[]);
        assert!(results.contains(&"test0".to_string()));
        assert!(results.contains(&"test3".to_string()));
        assert!(results.contains(&"1test".to_string()));
    }

    #[test]
    fn test_append_symbols() {
        let syms = vec!["!".to_string()];
        let results = apply_append("test", false, (0, 0), &syms, &[]);
        assert!(results.contains(&"test!".to_string()));
        assert!(results.contains(&"!test".to_string()));
    }
}
