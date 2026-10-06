"""config/pipeline.toml, read once per run."""

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    n_max: int
    profile: str
    spoken_weight: float
    contact: str


def load(path: Path) -> Config:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return Config(
        n_max=data["n_max"],
        profile=data["profile"],
        spoken_weight=data["frequency"]["spoken_weight"],
        contact=data["http"]["contact"],
    )
