"""Extraction logic for ``TE_TMHC_Configuration_File.xlsx``.

Phase-1 uses two independent parts of this workbook:
  * ``Model_Input_Mapping`` - traceable: for every command name pulled out of
    the Command List, add the matching row if one exists.
  * ``Tolerances`` - non-traceable: dumped wholesale (see
    ``nontraceable_extractor``).
"""
from __future__ import annotations

from typing import Any, Optional

from . import excel_utils as xu

MODEL_INPUT_MAPPING_SHEET = "Model_Input_Mapping"
COMMAND_NAME_HEADER_HINT = "command"


def find_model_input_mapping(wb, command_name: str) -> Optional[dict[str, Any]]:
    ws = xu.get_sheet(wb, MODEL_INPUT_MAPPING_SHEET)
    header_row = xu.find_header_row(ws, "Command Name", search_rows=5) \
        or xu.find_header_row(ws, "Command", search_rows=5) \
        or 1
    name_col = xu.find_column_containing(ws, header_row, COMMAND_NAME_HEADER_HINT)
    if name_col is None:
        return None
    return xu.find_row_by_value(ws, header_row, name_col, command_name)


def extract(wb_config, command_names: list[str]) -> dict[str, Any]:
    matches = []
    warnings: list[str] = []
    try:
        for name in command_names:
            row = find_model_input_mapping(wb_config, name)
            if row is not None:
                matches.append(row)
    except KeyError as exc:
        warnings.append(str(exc))
    result: dict[str, Any] = {"model_input_mapping_matches": matches}
    if warnings:
        result["_warnings"] = warnings
    return result
