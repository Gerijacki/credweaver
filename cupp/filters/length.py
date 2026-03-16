from typing import Iterator


def filter_length(stream: Iterator[str], min_len: int, max_len: int) -> Iterator[str]:
    for item in stream:
        if min_len <= len(item) <= max_len:
            yield item
