from credweaver.core.profile import DateInfo, Profile


def test_profile_token_extraction():
    p = Profile(name="john", surname="doe", pet_name="rex")
    tokens = p.to_tokens()
    assert "john" in tokens
    assert "doe" in tokens
    assert "rex" in tokens


def test_profile_date_formats():
    date = DateInfo(day=15, month=6, year=1990)
    formats = date.formats()
    assert "1990" in formats
    assert "90" in formats
    assert "15061990" in formats or any("15" in f for f in formats)


def test_profile_cleans_strings():
    p = Profile(name="  JOHN  ", surname="Doe")
    assert p.name == "john"
    assert p.surname == "doe"


def test_profile_empty_fields():
    p = Profile()
    assert p.to_tokens() == []
    assert p.to_date_tokens() == []


def test_profile_keywords():
    p = Profile(keywords=["crypto", "btc"])
    tokens = p.to_tokens()
    assert "crypto" in tokens
    assert "btc" in tokens
