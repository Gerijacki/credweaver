/// FNV-1a 64-bit hash
pub fn fnv1a(data: &[u8]) -> u64 {
    let mut hash: u64 = 0xcbf29ce484222325;
    for &byte in data {
        hash ^= byte as u64;
        hash = hash.wrapping_mul(0x100000001b3);
    }
    hash
}

/// DJB2 hash (64-bit variant)
pub fn djb2(data: &[u8]) -> u64 {
    let mut hash: u64 = 5381;
    for &byte in data {
        hash = hash.wrapping_mul(33).wrapping_add(byte as u64);
    }
    hash
}

/// Combine both hashes with a seed index to produce a bloom filter position.
pub fn hash_at(item: &str, seed: usize, size: usize) -> usize {
    let bytes = item.as_bytes();
    let h1 = fnv1a(bytes);
    let h2 = djb2(bytes);
    let combined = h1.wrapping_add((seed as u64).wrapping_mul(h2));
    (combined as usize) % size
}

/// Simple Bloom filter using bit array with k independent hash positions.
pub struct BloomFilter {
    bits: Vec<u64>,
    size: usize,
    k: usize,
}

impl BloomFilter {
    /// Create a new Bloom filter with given capacity and false-positive error rate.
    pub fn new(capacity: usize, error_rate: f64) -> Self {
        let ln2 = std::f64::consts::LN_2;
        let size = (-(capacity as f64) * error_rate.ln() / (ln2 * ln2)).ceil() as usize;
        let size = size.max(64);
        let k = ((size as f64 / capacity as f64) * ln2).round() as usize;
        let k = k.clamp(1, 20);
        let words = size.div_ceil(64);
        BloomFilter {
            bits: vec![0u64; words],
            size,
            k,
        }
    }

    /// Insert an item. Returns true if the item was probably already present.
    pub fn insert(&mut self, item: &str) -> bool {
        let mut already_present = true;
        for i in 0..self.k {
            let pos = hash_at(item, i, self.size);
            let word = pos / 64;
            let bit = pos % 64;
            if self.bits[word] & (1u64 << bit) == 0 {
                already_present = false;
                self.bits[word] |= 1u64 << bit;
            }
        }
        already_present
    }

    /// Check if item is probably present.
    pub fn contains(&self, item: &str) -> bool {
        for i in 0..self.k {
            let pos = hash_at(item, i, self.size);
            let word = pos / 64;
            let bit = pos % 64;
            if self.bits[word] & (1u64 << bit) == 0 {
                return false;
            }
        }
        true
    }
}

/// Wraps a BloomFilter to deduplicate a stream of strings.
pub struct StreamDeduplicator {
    filter: BloomFilter,
    pub removed_count: usize,
}

impl StreamDeduplicator {
    pub fn new(capacity: usize, error_rate: f64) -> Self {
        StreamDeduplicator {
            filter: BloomFilter::new(capacity, error_rate),
            removed_count: 0,
        }
    }

    /// Returns true if the item should be kept (not a duplicate).
    pub fn check_and_insert(&mut self, item: &str) -> bool {
        if self.filter.insert(item) {
            self.removed_count += 1;
            false
        } else {
            true
        }
    }
}

/// Deduplicate a Vec<String> using a HashSet (exact dedup).
pub fn dedup_exact(mut passwords: Vec<String>) -> Vec<String> {
    let mut seen = std::collections::HashSet::with_capacity(passwords.len());
    passwords.retain(|p| seen.insert(p.clone()));
    passwords
}

/// Deduplicate and return (unique_items, removed_count).
pub fn dedup_with_count(passwords: Vec<String>) -> (Vec<String>, usize) {
    let original_len = passwords.len();
    let deduped = dedup_exact(passwords);
    let removed = original_len - deduped.len();
    (deduped, removed)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bloom_insert_contains() {
        let mut bf = BloomFilter::new(1000, 0.01);
        assert!(!bf.insert("hello"));
        assert!(bf.insert("hello"));
        assert!(bf.contains("hello"));
        assert!(!bf.contains("world"));
    }

    #[test]
    fn test_dedup_exact() {
        let v = vec![
            "a".to_string(),
            "b".to_string(),
            "a".to_string(),
            "c".to_string(),
        ];
        let result = dedup_exact(v);
        assert_eq!(result.len(), 3);
    }

    #[test]
    fn test_fnv1a_djb2_different() {
        let h1 = fnv1a(b"test");
        let h2 = djb2(b"test");
        assert_ne!(h1, h2);
    }
}
