"""Load the modeled-assumption file. Outputs that use it are modeled estimates."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "model.yaml"


def parse_number(value: object) -> Fraction:
    text = str(value).strip()
    if "/" in text:
        left, right = text.split("/", 1)
        return Fraction(int(left), int(right))
    return Fraction(text)


@dataclass(frozen=True)
class Scales:
    booking_recovery_scale: Fraction
    contact_recovery_scale: Fraction
    margin_scale: Fraction
    cost_scale: Fraction


@dataclass(frozen=True)
class Config:
    seed: int
    window_days: int
    as_of: str
    margin_rate: Fraction
    handling_minutes: Fraction
    cost_per_minute: Fraction
    gap_ratio: Fraction
    sensitivity_shock: Fraction
    min_events: int
    max_duplicate_rate: Fraction
    max_null_rate: Fraction
    folio_per_night: int
    charge_per_night: int
    scenarios: dict[str, Scales]
    patterns: dict[str, dict]

    @property
    def priced_patterns(self) -> dict[str, dict]:
        return {
            name: spec
            for name, spec in self.patterns.items()
            if "booking_recovery" in spec and "contact_recovery" in spec
        }


def load_config(path: Path = CONFIG_PATH) -> Config:
    raw = yaml.safe_load(path.read_text())
    scenarios = {
        name: Scales(
            booking_recovery_scale=parse_number(item["booking_recovery_scale"]),
            contact_recovery_scale=parse_number(item["contact_recovery_scale"]),
            margin_scale=parse_number(item["margin_scale"]),
            cost_scale=parse_number(item["cost_scale"]),
        )
        for name, item in raw["scenarios"].items()
    }
    return Config(
        seed=int(raw["seed"]),
        window_days=int(raw["window_days"]),
        as_of=str(raw["as_of"]),
        margin_rate=parse_number(raw["margin_rate"]),
        handling_minutes=parse_number(raw["handling_minutes"]),
        cost_per_minute=parse_number(raw["cost_per_minute"]),
        gap_ratio=parse_number(raw["gap_ratio"]),
        sensitivity_shock=parse_number(raw["sensitivity_shock"]),
        min_events=int(raw["min_events"]),
        max_duplicate_rate=parse_number(raw["max_duplicate_rate"]),
        max_null_rate=parse_number(raw["max_null_rate"]),
        folio_per_night=int(raw["folio_per_night"]),
        charge_per_night=int(raw["charge_per_night"]),
        scenarios=scenarios,
        patterns=raw["patterns"],
    )
