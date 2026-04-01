from __future__ import annotations

from src.scorer import (
    _count_relevant_results,
    document_counts_for_scoring,
    scoring_aligned_results,
)


def test_document_counts_for_scoring_substring() -> None:
    doc = {"headline": "First Brands reports growth", "content": "More text"}
    assert document_counts_for_scoring(doc, "First Brands") is True
    assert document_counts_for_scoring(doc, "Acme Corp") is False


def test_document_counts_for_scoring_case_insensitive() -> None:
    doc = {"headline": "FIRST BRANDS update", "content": ""}
    assert document_counts_for_scoring(doc, "First Brands") is True


def test_count_relevant_results_matches_predicate() -> None:
    raw = {
        "entity_name": "Acme",
        "results": [
            {"headline": "Acme wins", "content": "x"},
            {"headline": "Other co", "content": "no match"},
            {"headline": "News", "content": "About acme here"},
        ],
    }
    assert len(scoring_aligned_results(raw)) == 2
    assert _count_relevant_results(raw) == 2
