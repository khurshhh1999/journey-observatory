"""Modeled opportunity. Revenue, margin, and support cost stay on separate lines."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from pipeline.config import Config, Scales


def _round_fraction(value: Fraction) -> int:
    if value >= 0:
        return int(value + Fraction(1, 2))
    return -int(-value + Fraction(1, 2))


def annualize(cents: int, window_days: int) -> int:
    return _round_fraction(Fraction(cents) * 365 / window_days)


@dataclass(frozen=True)
class MoneyLine:
    variant: str
    label: str
    cases: int
    dropoff_cases: int
    contacts: int
    revenue_cents: int
    margin_cents: int
    support_cents: int
    observed_loss_cents: int

    @property
    def modeled_cents(self) -> int:
        # Margin and avoidable support cost. Gross revenue is not added in.
        return self.margin_cents + self.support_cents


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    lines: tuple[MoneyLine, ...]
    contact_reduction: Fraction
    avoided_contacts: Fraction
    workload_contacts: int

    @property
    def revenue_cents(self) -> int:
        return sum(line.revenue_cents for line in self.lines)

    @property
    def margin_cents(self) -> int:
        return sum(line.margin_cents for line in self.lines)

    @property
    def support_cents(self) -> int:
        return sum(line.support_cents for line in self.lines)

    @property
    def modeled_cents(self) -> int:
        return self.margin_cents + self.support_cents

    @property
    def observed_loss_cents(self) -> int:
        return sum(line.observed_loss_cents for line in self.lines)


def _cap(rate: Fraction) -> Fraction:
    return min(Fraction(1), rate)


def price_variants(rows: list[dict], config: Config, scales: Scales) -> ScenarioResult:
    """Price the high-friction rows. `rows` already carry detected volumes."""
    lines: list[MoneyLine] = []
    avoided = Fraction(0)
    workload = 0
    margin_rate = config.margin_rate * scales.margin_scale
    minute_cents = config.handling_minutes * config.cost_per_minute * scales.cost_scale * 100
    for row in rows:
        spec = config.priced_patterns[row["variant"]]
        booking_recovery = _cap(parse_rate(spec["booking_recovery"]) * scales.booking_recovery_scale)
        contact_recovery = _cap(parse_rate(spec["contact_recovery"]) * scales.contact_recovery_scale)
        dropoff_value = Fraction(int(row["dropoff_value_cents"]))
        contacts = int(row["contacts"])
        in_window_revenue = dropoff_value * booking_recovery
        in_window_margin = in_window_revenue * margin_rate
        in_window_support = Fraction(contacts) * contact_recovery * minute_cents
        observed_margin = dropoff_value * config.margin_rate
        observed_support = Fraction(contacts) * config.handling_minutes * config.cost_per_minute * 100
        lines.append(
            MoneyLine(
                variant=row["variant"],
                label=str(spec["label"]),
                cases=int(row["cases"]),
                dropoff_cases=int(row["dropoff_cases"]),
                contacts=contacts,
                revenue_cents=annualize(_round_fraction(in_window_revenue), config.window_days),
                margin_cents=annualize(_round_fraction(in_window_margin), config.window_days),
                support_cents=annualize(_round_fraction(in_window_support), config.window_days),
                observed_loss_cents=_round_fraction(observed_margin + observed_support),
            )
        )
        avoided += Fraction(contacts) * contact_recovery
        workload += contacts
    reduction = avoided / workload if workload else Fraction(0)
    return ScenarioResult("priced", tuple(lines), reduction, avoided, workload)


def parse_rate(value: object) -> Fraction:
    from pipeline.config import parse_number

    return parse_number(value)


def sensitivity(rows: list[dict], config: Config) -> list[dict]:
    base = config.scenarios["base"]
    shock = config.sensitivity_shock
    names = (
        ("booking_recovery_scale", "Booking recovery"),
        ("contact_recovery_scale", "Contact recovery"),
        ("margin_scale", "Margin rate"),
        ("cost_scale", "Support cost"),
    )
    table = []
    base_total = price_variants(rows, config, base).modeled_cents
    for field, label in names:
        low_scales = _replace(base, field, getattr(base, field) * (1 - shock))
        high_scales = _replace(base, field, getattr(base, field) * (1 + shock))
        table.append(
            {
                "assumption": label,
                "low_cents": price_variants(rows, config, low_scales).modeled_cents,
                "base_cents": base_total,
                "high_cents": price_variants(rows, config, high_scales).modeled_cents,
            }
        )
    # Handling time moves support the same way as cost, and is its own assumption.
    low_minutes = _with_minutes(config, config.handling_minutes * (1 - shock))
    high_minutes = _with_minutes(config, config.handling_minutes * (1 + shock))
    table.append(
        {
            "assumption": "Handling time",
            "low_cents": price_variants(rows, low_minutes, base).modeled_cents,
            "base_cents": base_total,
            "high_cents": price_variants(rows, high_minutes, base).modeled_cents,
        }
    )
    return table


def _replace(scales: Scales, field: str, value: Fraction) -> Scales:
    data = {
        "booking_recovery_scale": scales.booking_recovery_scale,
        "contact_recovery_scale": scales.contact_recovery_scale,
        "margin_scale": scales.margin_scale,
        "cost_scale": scales.cost_scale,
    }
    data[field] = value
    return Scales(**data)


def _with_minutes(config: Config, minutes: Fraction) -> Config:
    return Config(
        seed=config.seed,
        window_days=config.window_days,
        as_of=config.as_of,
        margin_rate=config.margin_rate,
        handling_minutes=minutes,
        cost_per_minute=config.cost_per_minute,
        gap_ratio=config.gap_ratio,
        sensitivity_shock=config.sensitivity_shock,
        min_events=config.min_events,
        max_duplicate_rate=config.max_duplicate_rate,
        max_null_rate=config.max_null_rate,
        folio_per_night=config.folio_per_night,
        charge_per_night=config.charge_per_night,
        scenarios=config.scenarios,
        patterns=config.patterns,
    )
