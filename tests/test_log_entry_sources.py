"""A row whose sources share a field name must still be readable.

``_create_log`` splatted ``entries``, ``derived_entries`` and
``external_entries`` into one ``Log(**...)`` call, so a field present in two of
them raised ``TypeError: got multiple values for keyword argument`` — every read
of that context failed on a payload the server is entitled to return. A GTM
campaign row carried a SmartLead external binding whose name was also stored,
and it took a live outbound pipeline down.
"""

from __future__ import annotations

from unisdk.logs import _create_log


def _row(**sources) -> dict:
    return {"id": 1, "ts": None, **sources}


def test_a_name_in_two_sources_no_longer_raises() -> None:
    log = _create_log(
        _row(
            entries={"sl_max_new_leads_per_day": 20, "kept": "yes"},
            external_entries={"sl_max_new_leads_per_day": 40},
        ),
        "ctx",
        None,
    )
    assert log.entries["kept"] == "yes"


def test_external_overrides_stored() -> None:
    """Source order is the precedence, matching get_logs_federated."""

    log = _create_log(
        _row(
            entries={"cap": 1},
            derived_entries={"cap": 2},
            external_entries={"cap": 3},
        ),
        "ctx",
        None,
    )
    assert log.entries["cap"] == 3


def test_derived_overrides_stored_when_no_external() -> None:
    log = _create_log(
        _row(entries={"cap": 1}, derived_entries={"cap": 2}),
        "ctx",
        None,
    )
    assert log.entries["cap"] == 2


def test_absent_and_null_sources_are_tolerated() -> None:
    log = _create_log(
        _row(entries={"a": 1}, derived_entries=None, external_entries=None),
        "ctx",
        None,
    )
    assert log.entries == {"a": 1}
