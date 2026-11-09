from __future__ import annotations

from fractions import Fraction

import duckdb
import pyarrow as pa

from pipeline.config import load_config
from pipeline.quality import DataQualityError, assert_population
from pipeline.run import run


def test_pipeline_reproduces_the_internal_targets(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = run(write_site=False, root=tmp_path)
    base = result.scenarios["base"]
    upside = result.scenarios["upside"]
    downside = result.scenarios["downside"]

    assert result.events >= 60_000_000
    assert len(result.high_variants) == 9
    assert set(result.high_variants) == set(load_config().priced_patterns)
    modeled = base.modeled_cents / 100
    assert abs(modeled - 1_800_000) / 1_800_000 < 0.03
    assert base.contact_reduction == Fraction(24, 100)
    assert upside.modeled_cents > base.modeled_cents > downside.modeled_cents
    assert upside.contact_reduction > base.contact_reduction > downside.contact_reduction
    assert base.modeled_cents == base.margin_cents + base.support_cents
    assert base.revenue_cents > base.margin_cents
    assert base.revenue_cents != base.modeled_cents
    for row in result.sensitivity:
        assert row["high_cents"] > row["base_cents"] > row["low_cents"]


def test_quality_gate_rejects_a_null_spike():
    from dataclasses import replace
    from fractions import Fraction

    config = replace(load_config(), min_events=0, max_duplicate_rate=Fraction(1))
    con = duckdb.connect()
    con.register(
        "case_input",
        pa.table(
            {
                "reservation_id": [1, None],
                "property_id": [1, 1],
                "n_search": [1, 1],
                "n_raw_events": [10, 10],
                "n_duplicate_events": [0, 0],
            }
        ),
    )
    try:
        assert_population(con, config, expected_rows=2)
    except DataQualityError:
        return
    raise AssertionError("The gate should have stopped a null spike.")
