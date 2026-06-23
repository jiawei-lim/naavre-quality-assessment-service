from dataclasses import dataclass


@dataclass(frozen=True)
class Port:
    name: str
    type: str | None = None


@dataclass(frozen=True)
class Configuration:
    name: str
    assignation: str


@dataclass(frozen=True)
class Parameter:
    name: str
    type: str | None = None
    default_value: str | None = None


@dataclass(frozen=True)
class Secret:
    name: str
    type: str | None = None


@dataclass(frozen=True)
class Dependency:
    name: str
    module: str | None = None
    asname: str | None = None


@dataclass(frozen=True)
class BaseContainerImage:
    build: str | None = None
    runtime: str | None = None