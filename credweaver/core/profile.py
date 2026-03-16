import re

from pydantic import BaseModel, Field, field_validator


class DateInfo(BaseModel):
    day: int | None = Field(default=None, ge=1, le=31)
    month: int | None = Field(default=None, ge=1, le=12)
    year: int | None = Field(default=None, ge=1900, le=2025)

    def formats(self) -> list[str]:
        """Return all date format variations."""
        parts = []
        if self.day is not None:
            parts.append(f"{self.day:02d}")
        if self.month is not None:
            parts.append(f"{self.month:02d}")
        if self.year is not None:
            parts.append(str(self.year))
            parts.append(str(self.year)[-2:])
        combos = []
        d = f"{self.day:02d}" if self.day else ""
        m = f"{self.month:02d}" if self.month else ""
        y = str(self.year) if self.year else ""
        y2 = y[-2:] if y else ""
        for fmt in [
            f"{d}{m}{y}",
            f"{d}{m}{y2}",
            f"{y}{m}{d}",
            f"{d}/{m}/{y}",
            f"{m}{d}{y}",
        ]:
            stripped = fmt.strip("/")
            if stripped:
                combos.append(stripped)
        return list(set(parts + combos))


class Profile(BaseModel):
    name: str | None = None
    surname: str | None = None
    nickname: str | None = None
    birthdate: DateInfo | None = None
    partner_name: str | None = None
    partner_nickname: str | None = None
    partner_birthdate: DateInfo | None = None
    child_name: str | None = None
    child_nickname: str | None = None
    child_birthdate: DateInfo | None = None
    pet_name: str | None = None
    company: str | None = None
    keywords: list[str] = Field(default_factory=list)
    phone: str | None = None

    @field_validator(
        "name",
        "surname",
        "nickname",
        "partner_name",
        "partner_nickname",
        "child_name",
        "child_nickname",
        "pet_name",
        "company",
        mode="before",
    )
    @classmethod
    def clean_string(cls, v: object) -> str | None:
        if v is None:
            return v
        if isinstance(v, str):
            stripped = v.strip()
            return stripped.lower() if stripped else None
        return str(v)

    def to_tokens(self) -> list[str]:
        """Extract all non-null string tokens from profile."""
        tokens = []
        for field_val in [
            self.name,
            self.surname,
            self.nickname,
            self.partner_name,
            self.partner_nickname,
            self.child_name,
            self.child_nickname,
            self.pet_name,
            self.company,
        ]:
            if field_val:
                tokens.append(field_val)
        tokens.extend(self.keywords)
        if self.phone:
            digits = re.sub(r"\D", "", self.phone)
            if digits:
                tokens.append(digits)
        return [t for t in tokens if t]

    def to_date_tokens(self) -> list[str]:
        """Extract date format variations from all dates."""
        date_tokens = []
        for date in [self.birthdate, self.partner_birthdate, self.child_birthdate]:
            if date:
                date_tokens.extend(date.formats())
        return list(set(date_tokens))
