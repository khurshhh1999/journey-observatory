"""Write marts, the site extracts, and the three CSV files Tableau can sit on."""

from __future__ import annotations

import csv
import json
from fractions import Fraction
from pathlib import Path

import duckdb
import pyarrow as pa

from data_gen.catalog import PROPERTIES
from data_gen.expand import expand_row
from pipeline.config import Config, parse_number
from pipeline.proforma import ScenarioResult, price_variants, sensitivity

ROOT = Path(__file__).resolve().parents[1]


def _label(config: Config, variant: str) -> str:
    if variant == "clean":
        return "Completed stay"
    return str(config.patterns[variant]["label"])


def _outcome(variant: str, high: set[str]) -> tuple[str, str]:
    mapping = {
        "clean": ("completed", "Completed"),
        "voluntary_cancel": ("voluntary_exit", "Voluntary exit"),
        "voluntary_noshow": ("voluntary_exit", "Voluntary exit"),
        "policy_block": ("policy_block", "Policy block"),
        "telemetry_gap": ("telemetry_gap", "Telemetry gap"),
        "censored": ("censored", "Censored"),
    }
    if variant in mapping:
        return mapping[variant]
    if variant in high:
        return ("friction", "Friction")
    return ("other", "Other break")


def _ratio(value: object) -> dict[str, int]:
    number = value if isinstance(value, Fraction) else parse_number(value)
    return {"n": number.numerator, "d": number.denominator}


def _dollars(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"


def write_outputs(
    con: duckdb.DuckDBPyConnection,
    population: pa.Table,
    config: Config,
    scenarios: dict[str, ScenarioResult],
    *,
    export_dir: Path,
    site_dir: Path | None,
) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    stats = con.execute(
        """
        SELECT variant, cases, dropoff_cases, dropoff_rate, score, contacts,
               dropoff_value_cents, high_friction, rank
        FROM variant_stats
        ORDER BY rank
        """
    ).fetchall()
    high = {row[0] for row in stats if row[7] == 1}
    properties = {prop.id: prop for prop in PROPERTIES}
    sample = _sample_cases(con, population, config, high, properties)

    _write_journey(con, export_dir / "mart_journey.csv", properties, high)
    _write_friction(export_dir / "mart_friction.csv", stats, config)
    _write_opportunity(con, export_dir / "mart_opportunity.csv", config, high, properties)

    if site_dir is None:
        return
    site_dir.mkdir(parents=True, exist_ok=True)
    _write_site(con, site_dir, config, scenarios, stats, sample, high)


def _sample_cases(con, population, config, high, properties) -> list[dict]:
    ids = [
        row[0]
        for row in con.execute(
            """
            SELECT reservation_id FROM (
                SELECT reservation_id, variant,
                       row_number() OVER (PARTITION BY variant ORDER BY reservation_id) AS n
                FROM classified
            )
            WHERE n <= 4
            ORDER BY reservation_id
            """
        ).fetchall()
    ]
    variants = dict(
        con.execute(
            "SELECT reservation_id, variant FROM classified WHERE reservation_id IN (SELECT * FROM unnest(?))",
            [ids],
        ).fetchall()
    )
    import pyarrow.compute as pc

    subset = population.filter(pc.is_in(population.column("reservation_id"), value_set=pa.array(ids, type=pa.int64())))
    cases = []
    for row in subset.to_pylist():
        variant = variants[row["reservation_id"]]
        prop = properties[row["property_id"]]
        outcome, outcome_label = _outcome(variant, high)
        events = expand_row(row, cap_repeats=4)
        cases.append(
            {
                "id": f"R{row['reservation_id']:07d}",
                "reservationId": int(row["reservation_id"]),
                "propertyId": int(row["property_id"]),
                "propertyName": prop.name,
                "market": prop.market,
                "variant": variant,
                "variantLabel": _label(config, variant),
                "outcome": outcome,
                "outcomeLabel": outcome_label,
                "bookingValueCents": int(row["booking_value_cents"]),
                "nights": int(row["nights"]),
                "folioPosts": int(row["n_folio"]),
                "charges": int(row["n_charge"]),
                "events": [
                    {
                        "type": event["type"],
                        "label": event["label"],
                        "time": event["time"],
                        "seq": event["seq"],
                        "amountCents": event["amount_cents"],
                        "late": event["late"],
                        "duplicate": event["duplicate"],
                    }
                    for event in events
                ],
            }
        )
    cases.sort(key=lambda item: item["reservationId"])
    return cases


def _write_journey(con, path: Path, properties, high: set[str]) -> None:
    rows = con.execute(
        "SELECT property_id, variant, count(*) FROM classified GROUP BY 1, 2 ORDER BY 1, 2"
    ).fetchall()
    totals: dict[tuple[str, str, str], int] = {}
    for property_id, variant, cases in rows:
        prop = properties[property_id]
        _, outcome = _outcome(variant, high)
        key = (prop.name, prop.market, outcome)
        totals[key] = totals.get(key, 0) + int(cases)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["property", "market", "outcome", "cases"])
        for (name, market, outcome), cases in sorted(totals.items()):
            writer.writerow([name, market, outcome, cases])


def _write_friction(path: Path, stats, config: Config) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["variant", "label", "cases", "dropoff_cases", "dropoff_rate", "score", "contacts", "high_friction", "rank"]
        )
        for variant, cases, dropoff_cases, dropoff_rate, score, contacts, _value, high, rank in stats:
            writer.writerow(
                [
                    variant,
                    _label(config, variant),
                    int(cases),
                    int(dropoff_cases),
                    f"{float(dropoff_rate):.6f}",
                    int(score),
                    int(contacts),
                    int(high),
                    int(rank),
                ]
            )


def _write_opportunity(con, path: Path, config: Config, high: set[str], properties) -> None:
    rows = _property_rows(con, high)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "property",
                "market",
                "variant",
                "label",
                "cases",
                "dropoff_cases",
                "contacts",
                "modeled_revenue",
                "modeled_margin",
                "modeled_support_cost",
                "modeled_total",
                "observed_loss",
            ]
        )
        for row in rows:
            priced = price_variants([row], config, config.scenarios["base"])
            line = priced.lines[0]
            prop = properties[row["property_id"]]
            writer.writerow(
                [
                    prop.name,
                    prop.market,
                    row["variant"],
                    line.label,
                    line.cases,
                    line.dropoff_cases,
                    line.contacts,
                    _dollars(line.revenue_cents),
                    _dollars(line.margin_cents),
                    _dollars(line.support_cents),
                    _dollars(line.modeled_cents),
                    _dollars(line.observed_loss_cents),
                ]
            )


def _property_rows(con, high: set[str]) -> list[dict]:
    if not high:
        return []
    placeholders = ", ".join("?" for _ in high)
    found = con.execute(
        f"""
        SELECT property_id, variant, count(*) AS cases, sum(dropoff) AS dropoff_cases,
               sum(n_contact) AS contacts,
               sum(CASE WHEN dropoff = 1 THEN booking_value_cents ELSE 0 END) AS dropoff_value_cents
        FROM classified
        WHERE variant IN ({placeholders})
        GROUP BY 1, 2
        ORDER BY 2, 1
        """,
        list(high),
    ).fetchall()
    return [
        {
            "property_id": int(property_id),
            "variant": variant,
            "cases": int(cases),
            "dropoff_cases": int(dropoff_cases),
            "contacts": int(contacts),
            "dropoff_value_cents": int(dropoff_value_cents),
        }
        for property_id, variant, cases, dropoff_cases, contacts, dropoff_value_cents in found
    ]


def _line_payload(line) -> dict:
    return {
        "id": line.variant,
        "label": line.label,
        "cases": line.cases,
        "dropoffCases": line.dropoff_cases,
        "contacts": line.contacts,
        "revenueCents": line.revenue_cents,
        "marginCents": line.margin_cents,
        "supportCents": line.support_cents,
        "modeledCents": line.modeled_cents,
        "observedLossCents": line.observed_loss_cents,
    }


def _scenario_payload(result: ScenarioResult) -> dict:
    return {
        "revenueCents": result.revenue_cents,
        "marginCents": result.margin_cents,
        "supportCents": result.support_cents,
        "modeledCents": result.modeled_cents,
        "observedLossCents": result.observed_loss_cents,
        "contactReduction": float(result.contact_reduction),
        "avoidedContacts": float(result.avoided_contacts),
        "workloadContacts": result.workload_contacts,
    }


def _write_site(con, site_dir, config, scenarios, stats, sample, high) -> None:
    base = scenarios["base"]
    (site_dir / "explorer.json").write_text(
        json.dumps(
            {
                "properties": [
                    {"id": prop.id, "name": prop.name, "market": prop.market}
                    for prop in PROPERTIES
                ],
                "cases": sample,
            }
        )
    )
    evidence: dict[str, list] = {}
    for case in sample:
        evidence.setdefault(case["variant"], []).append(case)
    (site_dir / "friction.json").write_text(
        json.dumps(
            {
                "variants": [
                    {
                        "id": variant,
                        "label": _label(config, variant),
                        "rank": int(rank),
                        "cases": int(cases),
                        "dropoffCases": int(dropoff_cases),
                        "dropoffRate": float(dropoff_rate),
                        "score": int(score),
                        "contacts": int(contacts),
                        "high": bool(flag),
                        "evidence": evidence.get(variant, []) if flag else [],
                    }
                    for variant, cases, dropoff_cases, dropoff_rate, score, contacts, _value, flag, rank in stats
                ]
            }
        )
    )
    by_property = []
    for row in _property_rows(con, high):
        priced = price_variants([row], config, config.scenarios["base"])
        payload = _line_payload(priced.lines[0])
        payload["propertyId"] = row["property_id"]
        by_property.append(payload)
    shock = sensitivity(_portfolio_rows(stats, high), config)
    (site_dir / "proforma.json").write_text(
        json.dumps(
            {
                "properties": [
                    {"id": prop.id, "name": prop.name, "market": prop.market}
                    for prop in PROPERTIES
                ],
                "lines": [_line_payload(line) for line in base.lines],
                "totals": _scenario_payload(base),
                "sensitivity": shock,
                "range": {
                    "low": _scenario_payload(scenarios["downside"]),
                    "base": _scenario_payload(base),
                    "high": _scenario_payload(scenarios["upside"]),
                },
                "byProperty": by_property,
            }
        )
    )
    portfolio = _portfolio_rows(stats, high)
    (site_dir / "scenarios.json").write_text(
        json.dumps(
            {
                "windowDays": config.window_days,
                "marginRate": _ratio(config.margin_rate),
                "handlingMinutes": _ratio(config.handling_minutes),
                "costPerMinute": _ratio(config.cost_per_minute),
                "variants": [
                    {
                        "id": row["variant"],
                        "label": _label(config, row["variant"]),
                        "cases": row["cases"],
                        "dropoffCases": row["dropoff_cases"],
                        "contacts": row["contacts"],
                        "dropoffValueCents": row["dropoff_value_cents"],
                        "bookingRecovery": _ratio(config.priced_patterns[row["variant"]]["booking_recovery"]),
                        "contactRecovery": _ratio(config.priced_patterns[row["variant"]]["contact_recovery"]),
                    }
                    for row in portfolio
                ],
                "presets": {
                    name: {
                        "bookingRecoveryScale": float(scales.booking_recovery_scale),
                        "contactRecoveryScale": float(scales.contact_recovery_scale),
                        "marginScale": float(scales.margin_scale),
                        "costScale": float(scales.cost_scale),
                    }
                    for name, scales in config.scenarios.items()
                },
                "results": {name: _scenario_payload(result) for name, result in scenarios.items()},
            }
        )
    )


def _portfolio_rows(stats, high: set[str]) -> list[dict]:
    rows = []
    for variant, cases, dropoff_cases, _rate, _score, contacts, value, flag, _rank in stats:
        if not flag or variant not in high:
            continue
        rows.append(
            {
                "variant": variant,
                "cases": int(cases),
                "dropoff_cases": int(dropoff_cases),
                "contacts": int(contacts),
                "dropoff_value_cents": int(value),
            }
        )
    return rows
