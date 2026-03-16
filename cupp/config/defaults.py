DEFAULT_CONFIG_YAML = """
generation:
  max_depth: 3
  separators: ["", "_", "-", "."]
  threshold: 500
  use_rust_engine: true
  parallel_threads: null

mutations:
  leet:
    enabled: true
    level: 2
  case:
    modes: [lower, title, upper]
  append:
    numbers: true
    numbers_range: [0, 99]
    symbols: ["!", "@", "#", "123", "1234", "!@#"]
    years: true
    years_range: [1970, 2025]
  padding: false

filters:
  min_length: 6
  max_length: 20
  dedup: true
  bloom_capacity: 10000000
  bloom_error_rate: 0.001

strategies:
  enabled:
    - concatenation
    - date_based
    - keyboard_patterns
    - common_passwords
"""

KEYBOARD_PATTERNS = [
    "qwerty", "qwertyuiop", "asdfgh", "asdfghjkl", "zxcvbn", "zxcvbnm",
    "1qaz2wsx", "1q2w3e4r", "q1w2e3r4", "zaq1xsw2",
    "qazwsx", "qazwsxedc", "1q2w3e", "1qazxsw2",
    "123qwe", "qwe123", "abc123", "letmein", "iloveyou",
    "password", "passw0rd", "p@ssword", "p@ssw0rd",
    "master", "dragon", "monkey", "shadow",
    "111111", "121212", "123123", "696969", "654321",
    "0987654321", "9876543210",
]

TOP_COMMON_PASSWORDS = [
    "password", "123456", "password1", "abc123", "iloveyou",
    "admin", "letmein", "monkey", "1234567890", "dragon",
    "master", "sunshine", "princess", "welcome", "shadow",
    "superman", "michael", "football", "baseball", "soccer",
    "batman", "trustno1", "hello", "charlie", "donald",
    "password123", "qwerty", "123456789", "111111", "123123",
]
