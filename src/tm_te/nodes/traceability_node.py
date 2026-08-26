"""Node 1: extract every sheet that carries a traceability key
(requirement sheet id -> feature name -> feature id -> command name)."""
from __future__ import annotations

from ..extractors import command_extractor, config_extractor, excel_utils as xu
from ..extractors import requirements_extractor
from ..state import ExtractionState


def extract_traceability(state: ExtractionState) -> dict:
    errors = list(state.get("errors", []))
    req_sheet_id = state["req_sheet_id"]

    wb_requirements = xu.load_workbook(state["requirements_file"])
    requirements_data = requirements_extractor.extract(wb_requirements, req_sheet_id)

    feature_name = requirements_data.get("feature_name")
    command_data: dict = {}
    config_data: dict = {}

    if not feature_name:
        errors.append(
            f"Feature name for req sheet '{req_sheet_id}' not found in Index sheet; "
            "skipping Command List / Configuration File lookups."
        )
    else:
        wb_commands = xu.load_workbook(state["command_list_file"])
        command_data = command_extractor.extract(wb_commands, feature_name)

        wb_config = xu.load_workbook(state["config_file"])
        config_data = config_extractor.extract(wb_config, command_data.get("command_names", []))

    traceability_data = {
        "req_sheet_id": req_sheet_id,
        "feature_name": feature_name,
        "requirements": requirements_data,
        "commands": command_data,
        "configuration": config_data,
    }

    return {
        "feature_name": feature_name,
        "feature_id": command_data.get("feature_id"),
        "command_names": command_data.get("command_names", []),
        "traceability_data": traceability_data,
        "errors": errors,
    }
