from credweaver.filters.charset import filter_charset
from credweaver.filters.dedup import PythonBloomFilter, dedup_stream
from credweaver.filters.length import filter_length


def test_filter_length():
    words = ["hi", "hello", "superlongpassword", "ok"]
    result = list(filter_length(iter(words), 3, 10))
    assert "hello" in result
    assert "hi" not in result
    assert "superlongpassword" not in result


def test_filter_charset_digit():
    words = ["hello", "hello1", "HELLO1", "12345"]
    result = list(filter_charset(iter(words), ["digit"]))
    assert "hello1" in result
    assert "hello" not in result


def test_dedup_stream():
    words = ["abc", "def", "abc", "ghi", "def"]
    result = list(dedup_stream(iter(words)))
    assert len(result) == 3
    assert "abc" in result


def test_bloom_filter():
    bf = PythonBloomFilter(capacity=1000)
    assert not bf.add("hello")  # first time: not present
    assert bf.add("hello")  # second time: present
    assert "hello" in bf
    assert "world" not in bf
