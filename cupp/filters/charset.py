from typing import Iterator
import re

CHARSET_CHECKS = {
    "upper": re.compile(r"[A-Z]"),
    "lower": re.compile(r"[a-z]"),
    "digit": re.compile(r"\d"),
    "symbol": re.compile(r"[^A-Za-z0-9]"),
}


def filter_charset(stream: Iterator[str], required: list[str]) -> Iterator[str]:
    if not required:
        yield from stream
        return
    checks = [CHARSET_CHECKS[r] for r in required if r in CHARSET_CHECKS]
    for item in stream:
        if all(c.search(item) for c in checks):
            yield item
