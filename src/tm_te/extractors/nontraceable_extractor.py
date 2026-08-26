"""Extraction for sheets that have no direct traceability key and are pulled
wholesale instead of being filtered against a requirement/feature/command id:

  * Tolerances                          (TE_TMHC_Configuration_File.xlsx)
  * Compound Commands (Set) / (Verify)  (TE_TMHC_Compound_Commands.xlsx)
  * Library List                        (Keyword_Library_Description_Sheet.xlsx)
  * Custom Keyword&Library Details      (Keyword_Library_Description_Sheet.xlsx)
"""
from __future__ import annotations

from typing import Any

from . import excel_utils as xu

TOLERANCES_SHEET = "Tolerances"
COMPOUND_SET_SHEET = "Compound Commands (Set)"
COMPOUND_VERIFY_SHEET = "Compound Commands (Verify)"
LIBRARY_LIST_SHEET = "Library List"
CUSTOM_KEYWORD_SHEET = "Custom Keyword&Library Details"

LIBRARY_NAME_COL = 3  # column C
LIBRARY_DESC_COL = 4  # column D
LIBRARY_EXAMPLE_COL = 5  # column E

KEYWORD_LIBRARY_COL = 3  # column C
KEYWORD_TYPE_COL = 4  # column D
KEYWORD_METHOD_COL = 5  # column E
KEYWORD_EXAMPLE_COL = 6  # column F


def extract_tolerances(wb_config) -> list[dict[str, Any]]:
    ws = xu.get_sheet(wb_config, TOLERANCES_SHEET)
    return xu.sheet_to_records(ws, header_row=1)


def extract_compound_commands(wb_compound, sheet_name: str) -> list[dict[str, Any]]:
    """Each blank-row-separated block is one compound command table: its
    first row's first cell is the compound command name, the rest of that
    block is the table (second row = column headers, remainder = data)."""
    ws = xu.get_sheet(wb_compound, sheet_name)
    tables = []
    for block in xu.row_blocks(ws):
        if not block:
            continue
        name = block[0][0]
        if name in (None, ""):
            continue
        headers = [xu.norm_lower(h) or f"col_{i + 1}" for i, h in enumerate(block[1])] if len(block) > 1 else []
        rows = []
        for raw_row in block[2:]:
            if all(v is None or str(v).strip() == "" for v in raw_row):
                continue
            rows.append({
                (headers[i] if i < len(headers) and headers[i] else f"col_{i + 1}"): v
                for i, v in enumerate(raw_row)
            })
        tables.append({"compound_command_name": str(name).strip(), "rows": rows})
    return tables


def extract_library_list(wb_library) -> list[dict[str, Any]]:
    ws = xu.get_sheet(wb_library, LIBRARY_LIST_SHEET)
    entries = []
    for row in range(1, ws.max_row + 1):
        library = ws.cell(row=row, column=LIBRARY_NAME_COL).value
        description = ws.cell(row=row, column=LIBRARY_DESC_COL).value
        example = ws.cell(row=row, column=LIBRARY_EXAMPLE_COL).value
        if library in (None, ""):
            continue
        # Section-title rows carry only the library name with no
        # description/example alongside it; skip those.
        if description in (None, "") and example in (None, ""):
            continue
        entries.append({
            "library": str(library).strip(),
            "description": description,
            "example_usage": example,
        })
    return entries


def extract_custom_keywords(wb_library) -> list[dict[str, Any]]:
    ws = xu.get_sheet(wb_library, CUSTOM_KEYWORD_SHEET)
    entries = []
    for row in range(1, ws.max_row + 1):
        library = ws.cell(row=row, column=KEYWORD_LIBRARY_COL).value
        keyword_type = ws.cell(row=row, column=KEYWORD_TYPE_COL).value
        logical_method = ws.cell(row=row, column=KEYWORD_METHOD_COL).value
        example = ws.cell(row=row, column=KEYWORD_EXAMPLE_COL).value
        if library in (None, ""):
            continue
        if keyword_type in (None, "") and logical_method in (None, "") and example in (None, ""):
            continue
        entries.append({
            "library": str(library).strip(),
            "type": keyword_type,
            "logical_method": logical_method,
            "example": example,
        })
    return entries


def extract(wb_config, wb_compound, wb_library) -> dict[str, Any]:
    return {
        "tolerances": extract_tolerances(wb_config),
        "compound_commands_set": extract_compound_commands(wb_compound, COMPOUND_SET_SHEET),
        "compound_commands_verify": extract_compound_commands(wb_compound, COMPOUND_VERIFY_SHEET),
        "library_list": extract_library_list(wb_library),
        "custom_keywords": extract_custom_keywords(wb_library),
    }
