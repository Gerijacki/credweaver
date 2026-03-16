import gzip
from collections.abc import Iterator
from pathlib import Path

from credweaver.output.stats import GenerationStats, StatsTracker


def stream_to_file(
    stream: Iterator[str],
    output_path: Path,
    compress: bool = False,
) -> GenerationStats:
    tracker = StatsTracker()
    output_path = Path(output_path)

    use_gzip = compress or output_path.suffix == ".gz"

    if use_gzip:
        with gzip.open(output_path, "wt", encoding="utf-8") as f:
            for password in stream:
                f.write(password + "\n")
                tracker.stats.total_generated += 1
    else:
        with open(output_path, "w", encoding="utf-8", buffering=1 << 20) as f:
            for password in stream:
                f.write(password + "\n")
                tracker.stats.total_generated += 1

    return tracker.finish(str(output_path))
