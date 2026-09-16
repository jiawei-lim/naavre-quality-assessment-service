from enum import StrEnum


class QualityDimension(StrEnum):
    FUNCTIONAL_SUITABILITY = "Functional Suitability"
    MAINTAINABILITY = "Maintainability"
    SUSTAINABILITY = "Sustainability"
    FAIR = "FAIR"

    @classmethod
    def parse(cls, value: str) -> "QualityDimension":
        wanted = str(value).strip().casefold()
        for member in cls:
            if member.value.casefold() == wanted:
                return member
        raise ValueError(f"Unknown quality dimension: {value!r}")
