"""Shared helpers for DRINKOO API route modules."""

from __future__ import annotations

from typing import Any, Iterable, List, Mapping


def row_to_dict(row: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a SQLite row object into a plain dictionary."""

    return {key: row[key] for key in row.keys()}


def rows_to_dicts(rows: Iterable[Mapping[str, Any]]) -> List[dict[str, Any]]:
    """Convert SQLite row objects into plain dictionaries."""

    return [row_to_dict(row) for row in rows]
