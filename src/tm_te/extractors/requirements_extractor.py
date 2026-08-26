"""Extraction logic for ``System Requirements.xlsx``.

Steps (per the Phase-1 spec):
  1. Look up ``req_sheet_id`` (e.g. "019") in the "Index" sheet -> feature name.
  2. Open the sheet literally named ``req_sheet_id`` and keep only rows whose
     requirement-type column equals "Functional Requirement".
  3. In "Master Comm Matrix (CAN)", "Master List - App Parameter" and
     "Master Input Output Signals", find the header cell equal to
     ``req_sheet_id`` and keep only rows marked "O" (valid) in that column.
"""
from __future__ import annotations

from typing import Any, Optional

from . import excel_utils as xu

INDEX_SHEET = "Index"
COMM_MATRIX_SHEET = "Master Comm Matrix (CAN)"
APP_PARAMETER_SHEET = "Master List - App Parameter"
IO_SIGNALS_SHEET = "Master Input Output Signals"

REQUIREMENT_TYPE_HEADER_HINT = "requirement type"
FUNCTIONAL_REQUIREMENT_VALUE = "functional requirement"


def find_feature_name(wb, req_sheet_id: str) -> Optional[str]:
    """Search the Index sheet for ``req_sheet_id`` and return the feature name
    found in the same row."""
    ws = xu.get_sheet(wb, INDEX_SHEET)
    header_row = xu.find_header_row(ws, req_sheet_id, search_rows=ws.max_row) or 1
    # The Index sheet lists req-sheet-id -> feature-name as plain columns
    # (not a marker matrix), so search every row/col for the id and read the
    # "Feature Name" column of that row.
    feature_col = xu.find_column_containing(ws, 1, "feature name")
    id_col = xu.find_column_containing(ws, 1, "req") or 1
    for row in range(2, ws.max_row + 1):
        cell_val = ws.cell(row=row, column=id_col).value
        if str(cell_val).strip().lower() == str(req_sheet_id).strip().lower():
            if feature_col:
                return ws.cell(row=row, column=feature_col).value
            # fall back: return the first non-empty cell that isn't the id itself
            for col in range(1, ws.max_column + 1):
                val = ws.cell(row=row, column=col).value
                if col != id_col and val not in (None, ""):
                    return val
    return None


def extract_functional_requirements(wb, req_sheet_id: str) -> list[dict[str, Any]]:
    ws = xu.get_sheet(wb, req_sheet_id)
    header_row = xu.find_header_row(ws, "Req ID", search_rows=5) \
        or xu.find_header_row(ws, "Requirement ID", search_rows=5) \
        or 1
    req_type_col = xu.find_column_containing(ws, header_row, REQUIREMENT_TYPE_HEADER_HINT)
    if req_type_col is None:
        raise ValueError(
            f"Could not locate a '{REQUIREMENT_TYPE_HEADER_HINT}' column on sheet '{req_sheet_id}'"
        )
    records = xu.sheet_to_records(ws, header_row=header_row)
    header_names = xu.header_names(ws, header_row)
    req_type_key = header_names[req_type_col - 1]
    return [
        r for r in records
        if str(r.get(req_type_key, "")).strip().lower() == FUNCTIONAL_REQUIREMENT_VALUE
    ]


def extract_marker_sheet(wb, sheet_name: str, req_sheet_id: str) -> list[dict[str, Any]]:
    """Generic extractor for the Comm-Matrix / App-Parameter / IO-Signals sheets:
    find the column headed exactly ``req_sheet_id`` and keep rows marked 'O'."""
    ws = xu.get_sheet(wb, sheet_name)
    header_row = xu.find_header_row(ws, req_sheet_id)
    if header_row is None:
        raise ValueError(f"Header '{req_sheet_id}' not found on sheet '{sheet_name}'")
    marker_col = xu.find_column_in_row(ws, header_row, req_sheet_id)
    if marker_col is None:
        raise ValueError(f"Column '{req_sheet_id}' not found in header row of '{sheet_name}'")

    # Keep only "descriptive" columns (those that are not themselves O/X
    # marker columns for other requirement sheets) plus the matched column.
    descriptive_cols = _descriptive_columns(ws, header_row)
    return xu.filter_records_by_marker(
        ws, header_row, marker_col, xu.is_valid_marker, keep_cols=descriptive_cols
    )


def _descriptive_columns(ws, header_row: int) -> list[int]:
    """Columns whose data (sampled) is not exclusively O/X markers are treated
    as descriptive (Signal Name, Description, ...) and kept in every output row."""
    sample_rows = list(range(header_row + 1, min(header_row + 20, ws.max_row) + 1))
    cols = []
    for col in range(1, ws.max_column + 1):
        values = [xu.norm_lower(ws.cell(row=r, column=col).value) for r in sample_rows]
        non_empty = [v for v in values if v]
        if not non_empty:
            cols.append(col)
            continue
        if all(v in ("o", "x") for v in non_empty):
            continue  # marker column for some requirement sheet id
        cols.append(col)
    return cols


def extract(wb_requirements, req_sheet_id: str) -> dict[str, Any]:
    feature_name = find_feature_name(wb_requirements, req_sheet_id)
    functional_requirements = extract_functional_requirements(wb_requirements, req_sheet_id)

    result: dict[str, Any] = {
        "req_sheet_id": req_sheet_id,
        "feature_name": feature_name,
        "functional_requirements": functional_requirements,
    }

    for key, sheet_name in (
        ("comm_matrix", COMM_MATRIX_SHEET),
        ("app_parameter", APP_PARAMETER_SHEET),
        ("input_output_signals", IO_SIGNALS_SHEET),
    ):
        try:
            result[key] = extract_marker_sheet(wb_requirements, sheet_name, req_sheet_id)
        except (KeyError, ValueError) as exc:
            result[key] = []
            result.setdefault("_warnings", []).append(str(exc))

    return result
