import time
from dataclasses import dataclass


@dataclass
class GenerationStats:
    total_generated: int = 0
    duplicates_removed: int = 0
    filtered_out: int = 0
    elapsed_seconds: float = 0.0
    output_path: str = ""

    @property
    def passwords_per_second(self) -> float:
        if self.elapsed_seconds == 0:
            return 0.0
        return self.total_generated / self.elapsed_seconds

    def __str__(self) -> str:
        return (
            f"Generated: {self.total_generated:,} passwords\n"
            f"Duplicates removed: {self.duplicates_removed:,}\n"
            f"Filtered out: {self.filtered_out:,}\n"
            f"Time: {self.elapsed_seconds:.2f}s\n"
            f"Speed: {self.passwords_per_second:,.0f} pass/s\n"
            f"Output: {self.output_path}"
        )


class StatsTracker:
    def __init__(self) -> None:
        self._start = time.perf_counter()
        self.stats = GenerationStats()

    def finish(self, output_path: str = "") -> GenerationStats:
        self.stats.elapsed_seconds = time.perf_counter() - self._start
        self.stats.output_path = output_path
        return self.stats
