from typing import Iterator
from cupp.core.profile import Profile
from cupp.config.schema import CuppConfig
from cupp.strategies.registry import load_enabled_strategies
from cupp.mutations.leet import LeetMutation
from cupp.mutations.case import CaseMutation
from cupp.mutations.append import AppendMutation
from cupp.mutations.padding import PaddingMutation
from cupp.filters.length import filter_length
from cupp.filters.charset import filter_charset
from cupp.filters.dedup import dedup_stream


class Pipeline:
    """Orchestrates the full password generation pipeline."""

    def __init__(self, config: CuppConfig):
        self.config = config
        self._mutations = self._build_mutations()

    def _build_mutations(self):
        cfg = self.config.mutations
        muts = [
            LeetMutation(cfg),
            CaseMutation(cfg),
            AppendMutation(cfg),
        ]
        if cfg.padding:
            muts.append(PaddingMutation(cfg))
        return muts

    def _apply_mutations(self, stream: Iterator[str]) -> Iterator[str]:
        for password in stream:
            for mutation in self._mutations:
                yield from mutation.apply(password)

    def run(self, profile: Profile) -> Iterator[str]:
        # 1. Strategy layer: generate base candidates
        strategies = load_enabled_strategies(self.config)

        def base_stream() -> Iterator[str]:
            for strategy in strategies:
                yield from strategy.generate(profile)

        # 2. Try Rust engine if enabled
        if self.config.generation.use_rust_engine:
            stream = self._run_with_rust(profile, base_stream())
        else:
            stream = self._apply_mutations(base_stream())

        # 3. Filter by length
        fc = self.config.filters
        stream = filter_length(stream, fc.min_length, fc.max_length)

        # 4. Filter by charset
        if fc.required_charset:
            stream = filter_charset(stream, fc.required_charset)

        # 5. Dedup
        if fc.dedup:
            stream = dedup_stream(stream, fc.bloom_capacity)

        yield from stream

    def _run_with_rust(self, profile: Profile, fallback: Iterator[str]) -> Iterator[str]:
        try:
            import cupp_engine
            from cupp.core.token_extractor import TokenExtractor
            tokens = TokenExtractor().extract_with_variations(profile)
            cfg = self.config
            rust_config = {
                "separators": cfg.generation.separators,
                "max_depth": cfg.generation.max_depth,
                "min_length": cfg.filters.min_length,
                "max_length": cfg.filters.max_length,
                "leet_level": cfg.mutations.leet.level if cfg.mutations.leet.enabled else 0,
                "case_modes": cfg.mutations.case.modes,
                "append_numbers": cfg.mutations.append.numbers,
                "number_range": list(cfg.mutations.append.numbers_range),
                "append_symbols": cfg.mutations.append.symbols,
                "append_years": list(range(
                    cfg.mutations.append.years_range[0],
                    cfg.mutations.append.years_range[1] + 1,
                )) if cfg.mutations.append.years else [],
                "use_bloom": cfg.filters.dedup,
                "bloom_capacity": cfg.filters.bloom_capacity,
            }
            # Use collect_batch(4096) to reduce FFI overhead 4096x vs __next__
            rust_iter = cupp_engine.generate_combinations(tokens, rust_config)
            while True:
                batch = rust_iter.collect_batch(4096)
                if not batch:
                    break
                yield from batch
        except ImportError:
            # Fallback to Python pipeline if Rust engine not compiled
            yield from self._apply_mutations(fallback)
