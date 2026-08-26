"""LangGraph wiring for Phase 1: data extraction.

    START -> extract_traceability -> extract_nontraceable -> END
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes.nontraceable_node import extract_nontraceable
from .nodes.traceability_node import extract_traceability
from .state import ExtractionState


def build_extraction_graph():
    graph = StateGraph(ExtractionState)
    graph.add_node("extract_traceability", extract_traceability)
    graph.add_node("extract_nontraceable", extract_nontraceable)

    graph.add_edge(START, "extract_traceability")
    graph.add_edge("extract_traceability", "extract_nontraceable")
    graph.add_edge("extract_nontraceable", END)

    return graph.compile()
