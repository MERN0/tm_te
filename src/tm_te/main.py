"""CLI entry point for Phase 1 (data extraction).

Example:
    python -m tm_te.main \\
        --requirements-file "System Requirements.xlsx" \\
        --command-list-file "TE_TMHC_Command_List.xlsx" \\
        --config-file "TE_TMHC_Configuration_File.xlsx" \\
        --compound-commands-file "TE_TMHC_Compound_Commands.xlsx" \\
        --library-file "TE_TMHC_HILLS_Development & Testing_Keyword_Library_Description_Sheet.xlsx" \\
        --req-sheet-id 019 \\
        --output-dir output
"""
from __future__ import annotations

import argparse
import json
import sys

from .graph import build_extraction_graph
from .io_utils import save_extraction_output


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 1: extract test-case source data")
    parser.add_argument("--requirements-file", required=True)
    parser.add_argument("--command-list-file", required=True)
    parser.add_argument("--config-file", required=True)
    parser.add_argument("--compound-commands-file", required=True)
    parser.add_argument("--library-file", required=True)
    parser.add_argument("--req-sheet-id", required=True)
    parser.add_argument("--output-dir", default="output")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> dict:
    graph = build_extraction_graph()
    initial_state = {
        "requirements_file": args.requirements_file,
        "command_list_file": args.command_list_file,
        "config_file": args.config_file,
        "compound_commands_file": args.compound_commands_file,
        "library_file": args.library_file,
        "req_sheet_id": args.req_sheet_id,
        "output_dir": args.output_dir,
        "errors": [],
    }
    final_state = graph.invoke(initial_state)
    output_path = save_extraction_output(args.output_dir, args.req_sheet_id, final_state)
    final_state["output_path"] = output_path
    return final_state


def main(argv=None) -> int:
    args = parse_args(argv)
    final_state = run(args)
    print(f"Wrote {final_state['output_path']}")
    if final_state.get("errors"):
        print("Warnings/errors:", file=sys.stderr)
        for err in final_state["errors"]:
            print(f"  - {err}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
