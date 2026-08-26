"""Shared state schema for the LangGraph extraction pipeline.

Phase 1 covers two nodes:
  1. ``extract_traceability``  - everything that is traced back to a
     requirement sheet / feature: System Requirements.xlsx, the matching
     rows in TE_TMHC_Command_List.xlsx and TE_TMHC_Configuration_File.xlsx
     (Model_Input_Mapping only).
  2. ``extract_nontraceable``  - data that has no direct traceability key
     and is instead extracted wholesale: Tolerances, Compound Commands
     (Set/Verify) and the Keyword/Library description workbook.
"""
from __future__ import annotations

from typing import Any, Optional, TypedDict


class ExtractionState(TypedDict, total=False):
    # --- inputs (set once, before graph.invoke) ---
    requirements_file: str
    command_list_file: str
    config_file: str
    compound_commands_file: str
    library_file: str
    req_sheet_id: str
    output_dir: str

    # --- values derived while walking the traceability chain ---
    feature_name: Optional[str]
    feature_id: Optional[str]
    command_names: list[str]

    # --- node outputs ---
    traceability_data: dict[str, Any]
    nontraceable_data: dict[str, Any]

    # --- bookkeeping ---
    errors: list[str]
    output_path: str
