import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tm_te.graph import build_extraction_graph  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def fixtures_exist():
    if not (FIXTURES / "System Requirements.xlsx").exists():
        subprocess.run([sys.executable, str(FIXTURES / "build_fixtures.py")], check=True)


def _initial_state(req_sheet_id="019"):
    return {
        "requirements_file": str(FIXTURES / "System Requirements.xlsx"),
        "command_list_file": str(FIXTURES / "TE_TMHC_Command_List.xlsx"),
        "config_file": str(FIXTURES / "TE_TMHC_Configuration_File.xlsx"),
        "compound_commands_file": str(FIXTURES / "TE_TMHC_Compound_Commands.xlsx"),
        "library_file": str(
            FIXTURES / "TE_TMHC_HILLS_Development & Testing_Keyword_Library_Description_Sheet.xlsx"
        ),
        "req_sheet_id": req_sheet_id,
        "output_dir": "output",
        "errors": [],
    }


def test_traceability_chain_for_019():
    graph = build_extraction_graph()
    state = graph.invoke(_initial_state("019"))

    assert state["errors"] == []
    assert state["feature_name"] == "Adaptive Cruise Control"
    assert state["feature_id"] == "3"
    assert set(state["command_names"]) == {"SetCruiseSpeed", "EnableACC", "ApplyBrake"}

    req_data = state["traceability_data"]["requirements"]
    # Non-functional requirement row must be filtered out.
    req_ids = {r["Req ID"] for r in req_data["functional_requirements"]}
    assert req_ids == {"019-001", "019-003"}

    # Only rows marked "O" for column "019" survive; "X" rows are dropped.
    comm_signals = {r["Signal Name"] for r in req_data["comm_matrix"]}
    assert comm_signals == {"ACC_SetSpeed", "ACC_Enable"}
    assert "LKA_LaneOffset" not in comm_signals

    io_signals = {r["Signal Name"] for r in req_data["input_output_signals"]}
    assert io_signals == {"ACC_RadarDistance", "ACC_ThrottleCmd"}

    commands = state["traceability_data"]["commands"]
    assert {c["Command Name"] for c in commands["commands"]} == {
        "SetCruiseSpeed", "EnableACC", "ApplyBrake"
    }

    model_matches = state["traceability_data"]["configuration"]["model_input_mapping_matches"]
    assert {m["Command Name"] for m in model_matches} == {
        "SetCruiseSpeed", "EnableACC", "ApplyBrake"
    }


def test_nontraceable_data_extracted_wholesale():
    graph = build_extraction_graph()
    state = graph.invoke(_initial_state("019"))

    nontraceable = state["nontraceable_data"]
    assert len(nontraceable["tolerances"]) == 2

    set_names = {t["compound_command_name"] for t in nontraceable["compound_commands_set"]}
    assert set_names == {"SetCruiseAndEnable", "ApplyFullBrake"}
    verify_names = {t["compound_command_name"] for t in nontraceable["compound_commands_verify"]}
    assert verify_names == {"VerifyCruiseActive"}

    libraries = {entry["library"] for entry in nontraceable["library_list"]}
    assert libraries == {"CANLibrary", "ModelLibrary"}

    keywords = {entry["library"] for entry in nontraceable["custom_keywords"]}
    assert keywords == {"CANLibrary", "ModelLibrary"}


def test_second_requirement_sheet_010():
    graph = build_extraction_graph()
    state = graph.invoke(_initial_state("010"))

    assert state["feature_name"] == "Lane Keep Assist"
    assert state["feature_id"] == "4"
    assert state["command_names"] == ["SetLaneOffset"]

    req_data = state["traceability_data"]["requirements"]
    comm_signals = {r["Signal Name"] for r in req_data["comm_matrix"]}
    assert comm_signals == {"LKA_LaneOffset"}
