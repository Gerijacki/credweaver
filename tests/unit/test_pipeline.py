from credweaver.config.loader import merge_config
from credweaver.core.pipeline import Pipeline


def test_pipeline_generates_passwords(sample_profile, fast_config):
    pipeline = Pipeline(fast_config)
    results = list(pipeline.run(sample_profile))
    assert len(results) > 0
    for r in results:
        assert fast_config.filters.min_length <= len(r) <= fast_config.filters.max_length


def test_pipeline_dedup(sample_profile, fast_config):
    cfg_with_dedup = merge_config(fast_config, {"filters": {"dedup": True}})
    pipeline_dedup = Pipeline(cfg_with_dedup)
    results = list(pipeline_dedup.run(sample_profile))
    assert len(results) == len(set(results))


def test_pipeline_length_filter(sample_profile, fast_config):
    cfg = merge_config(fast_config, {"filters": {"min_length": 8, "max_length": 12}})
    pipeline = Pipeline(cfg)
    for p in pipeline.run(sample_profile):
        assert 8 <= len(p) <= 12
