"""System / human prompt templates for the extraction agent.

Phase 1's two nodes are deterministic (pure spreadsheet parsing) and do not
call an LLM, but the pipeline is designed as a LangGraph agent throughout,
so every node - deterministic or LLM-backed - is framed by the same
system/human prompt pair. Later phases (e.g. test-case generation from the
extracted JSON) plug an LLM in behind ``build_human_prompt`` without
changing this contract.
"""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

SYSTEM_PROMPT = """\
You are the Data Extraction Agent in a system-qualification test-case \
generation pipeline. Your job is to pull traceable, structured data out of \
a fixed set of Excel workbooks (System Requirements, Command List, \
Configuration File, Compound Commands, Keyword/Library Description) so \
that a later agent can synthesize qualification test cases from it.

Rules you must follow:
- Never invent data that is not present in the source workbooks.
- Preserve the traceability chain: requirement sheet id -> feature name -> \
feature id -> command name -> command definition -> model input mapping.
- Only rows explicitly marked valid ("O", checked/TRUE) are in scope; rows \
marked invalid ("X", unchecked/FALSE) must be dropped.
- Sheets with no direct traceability key (Tolerances, Compound Commands, \
Library List, Custom Keyword&Library Details) are extracted in full.
- Output must be valid JSON, organized by source sheet, ready for the next \
agent in the pipeline to consume.
"""

HUMAN_PROMPT_TEMPLATE = """\
Extract Phase-1 data for requirement sheet "{req_sheet_id}" from the \
following workbooks:
- System Requirements: {requirements_file}
- Command List: {command_list_file}
- Configuration File: {config_file}
- Compound Commands: {compound_commands_file}
- Keyword/Library Description: {library_file}

Return the traceable data (requirements, comm matrix, app parameter, IO \
signals, feature/command mapping, model input mapping) and the \
non-traceable data (tolerances, compound commands, library list, custom \
keywords) as two separate JSON objects.
"""

EXTRACTION_PROMPT = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", HUMAN_PROMPT_TEMPLATE)]
)


def build_extraction_prompt(state: dict) -> list:
    """Render the system/human prompt pair for the current run's inputs.

    Not invoked by the deterministic Phase-1 nodes today, but kept as the
    single place later LLM-backed nodes format their prompt from the graph
    state, so the whole pipeline shares one prompt-construction contract.
    """
    return EXTRACTION_PROMPT.format_messages(
        req_sheet_id=state.get("req_sheet_id", ""),
        requirements_file=state.get("requirements_file", ""),
        command_list_file=state.get("command_list_file", ""),
        config_file=state.get("config_file", ""),
        compound_commands_file=state.get("compound_commands_file", ""),
        library_file=state.get("library_file", ""),
    )
