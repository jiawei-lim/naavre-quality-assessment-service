from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BaseAsset:
    id: str
    title: str
    description: str = ""
    created: str | None = None
    modified: str | None = None
    owner: Any = None
    virtual_lab: Any = None
    shared_with_scopes: list[Any] = field(default_factory=list)
    shared_with_users: list[Any] = field(default_factory=list)
    raw_payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]):
        return cls(
            id=payload["id"],
            title=payload["title"],
            description=payload.get("description", ""),
            created=payload.get("created"),
            modified=payload.get("modified"),
            owner=payload.get("owner"),
            virtual_lab=payload.get("virtual_lab"),
            shared_with_scopes=payload.get("shared_with_scopes", []),
            shared_with_users=payload.get("shared_with_users", []),
            raw_payload=payload,
        )
