import tempfile
from pathlib import Path
import gzip
from cupp.output.file_writer import stream_to_file
from cupp.output.stats import GenerationStats, StatsTracker


def _make_stream(n=100):
    return (f"password{i}" for i in range(n))


def test_stream_to_file_creates_file():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        out = Path(f.name)
    stats = stream_to_file(_make_stream(50), out)
    assert out.exists()
    lines = out.read_text().strip().split("\n")
    assert len(lines) == 50
    assert stats.total_generated == 50
    out.unlink()


def test_stream_to_file_gzip():
    with tempfile.NamedTemporaryFile(suffix=".txt.gz", delete=False) as f:
        out = Path(f.name)
    stream_to_file(_make_stream(100), out, compress=True)
    assert out.exists()
    with gzip.open(out, "rt") as f:
        lines = f.read().strip().split("\n")
    assert len(lines) == 100
    out.unlink()


def test_stats_tracker():
    import time
    tracker = StatsTracker()
    time.sleep(0.01)
    stats = tracker.finish(output_path="test.txt")
    assert stats.elapsed_seconds > 0
    assert stats.output_path == "test.txt"


def test_stats_passwords_per_second():
    stats = GenerationStats(total_generated=1000, elapsed_seconds=1.0)
    assert stats.passwords_per_second == 1000.0


def test_stats_zero_elapsed():
    stats = GenerationStats(total_generated=1000, elapsed_seconds=0.0)
    assert stats.passwords_per_second == 0.0
