from collections.abc import Generator, Iterator


class PythonBloomFilter:
    """Simple bloom filter using two hash functions."""

    def __init__(self, capacity: int = 10_000_000, error_rate: float = 0.001):
        import math

        self.size = int(-capacity * math.log(error_rate) / (math.log(2) ** 2))
        self.k = max(1, int(self.size / capacity * math.log(2)))
        self.bits = bytearray(self.size // 8 + 1)

    def _hashes(self, item: str) -> Generator[int, None, None]:
        h1 = hash(item) & 0x7FFFFFFF
        h2 = hash(item[::-1] + "salt") & 0x7FFFFFFF
        for i in range(self.k):
            yield (h1 + i * h2) % self.size

    def add(self, item: str) -> bool:
        """Returns True if item was already present (probable)."""
        positions = list(self._hashes(item))
        probably_present = all(self.bits[p // 8] & (1 << (p % 8)) for p in positions)
        for p in positions:
            self.bits[p // 8] |= 1 << (p % 8)
        return probably_present

    def __contains__(self, item: str) -> bool:
        return all(self.bits[p // 8] & (1 << (p % 8)) for p in self._hashes(item))


def dedup_stream(stream: Iterator[str], capacity: int = 10_000_000) -> Iterator[str]:
    bloom = PythonBloomFilter(capacity)
    for item in stream:
        if not bloom.add(item):
            yield item
