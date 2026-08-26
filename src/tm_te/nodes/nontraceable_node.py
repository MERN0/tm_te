"""Node 2: extract sheets with no traceability key - pulled wholesale
(Tolerances, Compound Commands Set/Verify, Library List, Custom Keywords)."""
from __future__ import annotations

from ..extractors import excel_utils as xu
from ..extractors import nontraceable_extractor
from ..state import ExtractionState


def extract_nontraceable(state: ExtractionState) -> dict:
    errors = list(state.get("errors", []))

    wb_config = xu.load_workbook(state["config_file"])
    wb_compound = xu.load_workbook(state["compound_commands_file"])
    wb_library = xu.load_workbook(state["library_file"])

    try:
        nontraceable_data = nontraceable_extractor.extract(wb_config, wb_compound, wb_library)
    except (KeyError, ValueError) as exc:
        errors.append(str(exc))
        nontraceable_data = {}

    return {"nontraceable_data": nontraceable_data, "errors": errors}
