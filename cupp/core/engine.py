from pathlib import Path
from typing import Iterator
from cupp.core.profile import Profile
from cupp.core.pipeline import Pipeline
from cupp.config.loader import load_config
from cupp.config.schema import CuppConfig
from cupp.output.stats import GenerationStats


class Engine:
    """Main entry point for CUPP v2 generation."""

    def __init__(
        self,
        config: CuppConfig | None = None,
        config_path: Path | None = None,
    ):
        if config is not None:
            self.config = config
        else:
            self.config = load_config(config_path)
        self.pipeline = Pipeline(self.config)

    def generate(self, profile: Profile) -> Iterator[str]:
        """Generate passwords for a profile. Returns a lazy iterator."""
        return self.pipeline.run(profile)

    def generate_to_file(self, profile: Profile, output_path: Path) -> GenerationStats:
        from cupp.output.file_writer import stream_to_file
        return stream_to_file(self.generate(profile), output_path)

    def rust_available(self) -> bool:
        try:
            import cupp_engine  # noqa: F401
            return True
        except ImportError:
            return False
