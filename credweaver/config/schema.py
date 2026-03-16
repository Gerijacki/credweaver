from pydantic import BaseModel, Field, field_validator


class LeetConfig(BaseModel):
    enabled: bool = True
    level: int = Field(default=2, ge=1, le=3)


class CaseConfig(BaseModel):
    modes: list[str] = ["lower", "title", "upper"]

    @field_validator("modes")
    @classmethod
    def validate_modes(cls, v: list[str]) -> list[str]:
        valid = {"lower", "upper", "title", "toggle", "camel"}
        for m in v:
            if m not in valid:
                raise ValueError(f"Invalid case mode: {m}")
        return v


class AppendConfig(BaseModel):
    numbers: bool = True
    numbers_range: tuple[int, int] = (0, 99)
    symbols: list[str] = ["!", "@", "#", "123", "!@#"]
    years: bool = True
    years_range: tuple[int, int] = (1970, 2025)


class MutationConfig(BaseModel):
    leet: LeetConfig = Field(default_factory=LeetConfig)
    case: CaseConfig = Field(default_factory=CaseConfig)
    append: AppendConfig = Field(default_factory=AppendConfig)
    padding: bool = False


class FilterConfig(BaseModel):
    min_length: int = Field(default=6, ge=1)
    max_length: int = Field(default=20, le=100)
    dedup: bool = True
    bloom_capacity: int = 10_000_000
    bloom_error_rate: float = 0.001
    required_charset: list[str] | None = None


class GenerationConfig(BaseModel):
    max_depth: int = Field(default=3, ge=1, le=5)
    separators: list[str] = ["", "_", "-", ".", "123"]
    threshold: int = 500
    use_rust_engine: bool = True
    parallel_threads: int | None = None


class StrategyConfig(BaseModel):
    enabled: list[str] = ["concatenation", "date_based", "keyboard_patterns", "common_passwords"]


class CredWeaverConfig(BaseModel):
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    mutations: MutationConfig = Field(default_factory=MutationConfig)
    filters: FilterConfig = Field(default_factory=FilterConfig)
    strategies: StrategyConfig = Field(default_factory=StrategyConfig)
