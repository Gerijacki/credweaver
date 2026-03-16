import pytest

from credweaver.core.profile import DateInfo, Profile
from credweaver.core.token_extractor import TokenExtractor


@pytest.fixture
def extractor():
    return TokenExtractor()


def test_extract_base_tokens(extractor):
    profile = Profile(name="alice", surname="smith", pet_name="fluffy")
    result = extractor.extract(profile)
    assert "alice" in result["base"]
    assert "smith" in result["base"]
    assert "fluffy" in result["base"]


def test_extract_date_tokens(extractor):
    profile = Profile(birthdate=DateInfo(day=1, month=3, year=1985))
    result = extractor.extract(profile)
    assert len(result["dates"]) > 0
    assert any("1985" in d for d in result["dates"])


def test_extract_all_combines(extractor):
    profile = Profile(name="alice", birthdate=DateInfo(year=1990))
    result = extractor.extract(profile)
    assert len(result["all"]) >= len(result["base"])


def test_extract_with_variations_includes_case(extractor):
    profile = Profile(name="alice")
    variations = extractor.extract_with_variations(profile)
    assert "alice" in variations
    assert "Alice" in variations
    assert "ALICE" in variations


def test_extract_with_variations_includes_reverse(extractor):
    profile = Profile(name="alice")
    variations = extractor.extract_with_variations(profile)
    assert "ecila" in variations


def test_empty_profile(extractor):
    profile = Profile()
    result = extractor.extract(profile)
    assert result["base"] == []
    assert result["dates"] == []
    assert result["all"] == []


def test_phone_extracted_as_digits(extractor):
    profile = Profile(phone="+34 555-1234")
    result = extractor.extract(profile)
    assert any(d.isdigit() for d in result["base"])
