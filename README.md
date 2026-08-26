# tm_te

LangGraph agent that generates system qualification test cases from a fixed
set of system requirements / configuration workbooks.

## Phase 1: data extraction

The pipeline starts with a two-node LangGraph graph that pulls all of the
data a later test-case-generation node will need, given a requirement sheet
id (e.g. `019`):

```
START -> extract_traceability -> extract_nontraceable -> END
```

**`extract_traceability`** walks the traceability chain end to end:

1. `System Requirements.xlsx` / `Index` — look up the requirement sheet id
   to get the feature name.
2. `System Requirements.xlsx` / `<req_sheet_id>` — keep only rows marked
   `Functional Requirement`.
3. `System Requirements.xlsx` / `Master Comm Matrix (CAN)`,
   `Master List - App Parameter`, `Master Input Output Signals` — find the
   header column equal to `<req_sheet_id>` and keep only rows marked `O`
   (drop `X`).
4. `TE_TMHC_Command_List.xlsx` / `Feature_ID_Mapping` — look up the feature
   name to get the feature id.
5. `TE_TMHC_Command_List.xlsx` / `Recorder_Signal_Feature`,
   `SDO_Signal_Feature` — find the column headed by the feature id and keep
   the checked/`TRUE` rows (first 4 columns only), then read out the
   `Command Name`s.
6. `TE_TMHC_Command_List.xlsx` / `Command List` — pull the full command
   definition for every command name found above.
7. `TE_TMHC_Configuration_File.xlsx` / `Model_Input_Mapping` — add any row
   whose command name matches.

**`extract_nontraceable`** pulls the sheets that have no traceability key,
in full: `Tolerances` (Configuration File), `Compound Commands (Set)` /
`(Verify)` (parsed as blank-row-separated tables, first cell of each table
= compound command name), and `Library List` / `Custom Keyword&Library
Details` (Keyword/Library Description workbook — scattered `library /
description / example` blocks starting in column C).

Both nodes' output is merged and written to
`output/<req_sheet_id>_extraction.json`.

The whole pipeline is framed as an agent via `src/tm_te/prompts.py`
(system + human prompt pair). Phase 1's two nodes are deterministic
spreadsheet parsing and don't call an LLM; later phases (test-case
synthesis from this JSON) reuse the same prompt contract with an
LLM-backed node.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e . -r requirements.txt
```

## Running

```bash
python -m tm_te.main \
  --requirements-file "System Requirements.xlsx" \
  --command-list-file "TE_TMHC_Command_List.xlsx" \
  --config-file "TE_TMHC_Configuration_File.xlsx" \
  --compound-commands-file "TE_TMHC_Compound_Commands.xlsx" \
  --library-file "TE_TMHC_HILLS_Development & Testing_Keyword_Library_Description_Sheet.xlsx" \
  --req-sheet-id 019 \
  --output-dir output
```

## Testing

The real source workbooks aren't in this repo, so `tests/fixtures/build_fixtures.py`
generates small synthetic xlsx files that mirror the documented sheet
layouts (Index / req sheet / Comm Matrix / App Parameter / IO Signals /
Feature_ID_Mapping / Recorder & SDO Signal Feature / Command List /
Model_Input_Mapping / Tolerances / Compound Commands / Library List /
Custom Keyword&Library Details). Run:

```bash
pytest tests/
```

**These fixtures encode assumptions about column names and layout that
haven't been checked against the real files** (e.g. that the Index sheet
has a "Req Sheet" / "Feature Name" header, that Command List has a
"Command Name" column, exact header wording elsewhere). Run Phase 1 against
the real workbooks next and report any sheet/column name mismatches —
the extractors in `src/tm_te/extractors/` search by header text rather than
fixed cell coordinates, so a mismatch is usually a one-line fix (the hint
string passed to `find_column_containing`/`find_header_row`).
