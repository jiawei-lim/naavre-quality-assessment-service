from enum import StrEnum


class QualityDimension(StrEnum):
    """Canonical names of the quality dimensions checks are grouped under.

    Declaration order is the order results appear in an assessment response.
    """
    FUNCTIONAL_SUITABILITY = "Functional Suitability"
    MAINTAINABILITY = "Maintainability"
    SUSTAINABILITY = "Sustainability"
    FAIR = "FAIR"

    @classmethod
    def parse(cls, value: str) -> "QualityDimension":
        """Case-insensitive lookup by display name."""
        wanted = str(value).strip().casefold()
        for member in cls:
            if member.value.casefold() == wanted:
                return member
        raise ValueError(f"Unknown quality dimension: {value!r}")
