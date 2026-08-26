"""Helpers for saving the extraction pipeline's output."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def save_extraction_output(output_dir: str, req_sheet_id: str, state: dict) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "req_sheet_id": req_sheet_id,
        "feature_name": state.get("feature_name"),
        "feature_id": state.get("feature_id"),
        "traceability_data": state.get("traceability_data", {}),
        "nontraceable_data": state.get("nontraceable_data", {}),
        "errors": state.get("errors", []),
    }
    out_path = Path(output_dir) / f"{req_sheet_id}_extraction.json"
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return str(out_path)
