"""Extraction logic for ``TE_TMHC_Command_List.xlsx``.

Steps:
  1. Look up ``feature_name`` in "Feature_ID_Mapping" -> feature id (e.g. "3").
  2. In "Recorder_Signal_Feature" and "SDO_Signal_Feature", find the column
     headed by that feature id and keep the checked/true rows, first 4
     columns only.
  3. Collect the "Command Name" values out of those rows and look each one
     up in the "Command List" sheet to pull the full command definition.
"""
from __future__ import annotations

from typing import Any, Optional

from . import excel_utils as xu

FEATURE_ID_MAPPING_SHEET = "Feature_ID_Mapping"
RECORDER_SIGNAL_FEATURE_SHEET = "Recorder_Signal_Feature"
SDO_SIGNAL_FEATURE_SHEET = "SDO_Signal_Feature"
COMMAND_LIST_SHEET = "Command List"

FEATURE_NAME_HEADER_HINT = "feature name"
ID_HEADER_HINT = "id"
COMMAND_NAME_HEADER_HINT = "command name"
FIRST_N_SIGNAL_COLUMNS = 4


def find_feature_id(wb, feature_name: str) -> Optional[str]:
    ws = xu.get_sheet(wb, FEATURE_ID_MAPPING_SHEET)
    name_col = xu.find_column_containing(ws, 1, FEATURE_NAME_HEADER_HINT) or 1
    id_col = xu.find_column_containing(ws, 1, ID_HEADER_HINT) or 2
    for row in range(2, ws.max_row + 1):
        if xu.norm_lower(ws.cell(row=row, column=name_col).value) == xu.norm_lower(feature_name):
            value = ws.cell(row=row, column=id_col).value
            return str(value).strip() if value is not None else None
    return None


def extract_checked_signals(wb, sheet_name: str, feature_id: str) -> list[dict[str, Any]]:
    """Filter a signal-feature sheet down to the rows checked TRUE for
    ``feature_id``, keeping only the first 4 (descriptive) columns."""
    ws = xu.get_sheet(wb, sheet_name)
    header_row = xu.find_header_row(ws, feature_id)
    if header_row is None:
        raise ValueError(f"Header '{feature_id}' not found on sheet '{sheet_name}'")
    marker_col = xu.find_column_in_row(ws, header_row, feature_id)
    if marker_col is None:
        raise ValueError(f"Column '{feature_id}' not found in header row of '{sheet_name}'")
    keep_cols = list(range(1, min(FIRST_N_SIGNAL_COLUMNS, ws.max_column) + 1))
    return xu.filter_records_by_marker(ws, header_row, marker_col, xu.is_truthy, keep_cols=keep_cols)


def _command_names_from_records(records: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for record in records:
        for key, value in record.items():
            if COMMAND_NAME_HEADER_HINT in key.lower() and value not in (None, ""):
                names.append(str(value).strip())
                break
    return names


def find_command_definition(wb, command_name: str) -> Optional[dict[str, Any]]:
    ws = xu.get_sheet(wb, COMMAND_LIST_SHEET)
    header_row = xu.find_header_row(ws, "Command Name", search_rows=5) or 1
    name_col = xu.find_column_containing(ws, header_row, COMMAND_NAME_HEADER_HINT)
    if name_col is None:
        raise ValueError(f"No '{COMMAND_NAME_HEADER_HINT}' column found in '{COMMAND_LIST_SHEET}'")
    return xu.find_row_by_value(ws, header_row, name_col, command_name)


def extract(wb_command_list, feature_name: str) -> dict[str, Any]:
    result: dict[str, Any] = {"feature_name": feature_name}
    warnings: list[str] = []

    feature_id = find_feature_id(wb_command_list, feature_name)
    result["feature_id"] = feature_id
    if feature_id is None:
        warnings.append(f"Feature '{feature_name}' not found in {FEATURE_ID_MAPPING_SHEET}")
        result["recorder_signals"] = []
        result["sdo_signals"] = []
        result["command_names"] = []
        result["commands"] = []
        if warnings:
            result["_warnings"] = warnings
        return result

    signal_sets: dict[str, list[dict[str, Any]]] = {}
    for key, sheet_name in (
        ("recorder_signals", RECORDER_SIGNAL_FEATURE_SHEET),
        ("sdo_signals", SDO_SIGNAL_FEATURE_SHEET),
    ):
        try:
            signal_sets[key] = extract_checked_signals(wb_command_list, sheet_name, feature_id)
        except (KeyError, ValueError) as exc:
            signal_sets[key] = []
            warnings.append(str(exc))
    result.update(signal_sets)

    command_names: list[str] = []
    for records in signal_sets.values():
        for name in _command_names_from_records(records):
            if name not in command_names:
                command_names.append(name)
    result["command_names"] = command_names

    commands = []
    for name in command_names:
        try:
            definition = find_command_definition(wb_command_list, name)
        except ValueError as exc:
            warnings.append(str(exc))
            break
        if definition is None:
            warnings.append(f"Command '{name}' not found in {COMMAND_LIST_SHEET}")
            continue
        commands.append(definition)
    result["commands"] = commands

    if warnings:
        result["_warnings"] = warnings
    return result
