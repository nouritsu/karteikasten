"""config/pipeline.toml, read once per run."""

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    n_max: int
    profile: str
    spoken_weight: float
    epsilon: float
    contact: str
    recording_author: str = ""
    recording_license: str = ""


def load(path: Path) -> Config:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return Config(
        n_max=data["n_max"],
        profile=data["profile"],
        spoken_weight=data["frequency"]["spoken_weight"],
        epsilon=data["frequency"].get("epsilon", 0.1),
        contact=data["http"]["contact"],
        recording_author=data.get("recordings", {}).get("author", ""),
        recording_license=data.get("recordings", {}).get("license", ""),
    )
