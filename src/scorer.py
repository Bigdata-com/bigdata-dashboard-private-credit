from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.entities import ALL_ENTITIES, EntityDict
from config.paths import RAW_CACHE_DIR, SCORES_CSV, SCORING_AUDIT_DIR
from config.topics import TOPICS, TopicDict
from src.utils import console, sanitize_filename, setup_logger

logger = setup_logger(__name__)

RAW_OUTPUT_DIR = RAW_CACHE_DIR
SCORES_OUTPUT = SCORES_CSV


def document_counts_for_scoring(doc: dict[str, Any], entity_name: str) -> bool:
    """True if this search hit is counted in heatmap/topic scores for the entity.

    Matches the same rule as per-topic counts: entity name appears in headline or body
    (case-insensitive substring).
    """
    text = (doc.get("headline", "") + " " + doc.get("content", "")).lower()
    return entity_name.lower() in text


def scoring_aligned_results(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Search hits that are counted toward the entity × topic score (and audit tab)."""
    name = str(raw["entity_name"])
    return [d for d in raw.get("results", []) if document_counts_for_scoring(d, name)]


def _load_raw_result(
    entity: EntityDict, topic: TopicDict, raw_dir: Path | None = None,
) -> dict[str, Any] | None:
    entity_slug = sanitize_filename(str(entity["name"]))
    topic_slug = sanitize_filename(str(topic["topic_name"]))
    base = raw_dir if raw_dir is not None else RAW_OUTPUT_DIR
    path = base / f"{entity_slug}_{topic_slug}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _count_relevant_results(raw: dict[str, Any]) -> int:
    """Count results that actually mention the entity name in headline or content.

    The API always returns up to `limit` documents via semantic search, so raw
    n_results is usually saturated at the limit. Counting entity mentions in the
    returned text gives a true relevance signal that differentiates entities.
    """
    return len(scoring_aligned_results(raw))


def _clear_scoring_audit_cache(audit_dir: Path | None = None) -> None:
    """Remove prior scoring-audit JSON so stale (entity, topic) files cannot linger."""
    target = audit_dir if audit_dir is not None else SCORING_AUDIT_DIR
    if not target.exists():
        target.mkdir(parents=True, exist_ok=True)
        return
    for f in target.glob("*.json"):
        f.unlink()


def _write_scoring_audit(
    entity_slug: str,
    topic_slug: str,
    entity_name: str,
    topic_name: str,
    polarity: str,
    aligned: list[dict[str, Any]],
    audit_dir: Path | None = None,
) -> None:
    """Persist the exact rows counted for this entity × topic (source for HTML audit)."""
    target = audit_dir if audit_dir is not None else SCORING_AUDIT_DIR
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{entity_slug}_{topic_slug}.json"
    payload: dict[str, Any] = {
        "entity_name": entity_name,
        "topic_name": topic_name,
        "topic_polarity": polarity,
        "n_counted": len(aligned),
        "results": aligned,
    }
    path.write_text(json.dumps(payload, indent=2, default=str))


def _get_applicable_topics(layer: str) -> list[TopicDict]:
    return [t for t in TOPICS if layer in t["applies_to"]]


def compute_scores(
    entities: list[EntityDict] | None = None,
    raw_dir: Path | None = None,
    audit_dir: Path | None = None,
    scores_csv: Path | None = None,
) -> pd.DataFrame:
    """Aggregate raw search results into entity-level scores.

    Returns a DataFrame with per-entity scores and per-topic mention counts.
    When raw_dir / audit_dir / scores_csv are supplied the scorer works in an
    isolated directory (used by the web server for custom pipeline runs).
    """
    target_entities = entities or ALL_ENTITIES
    rows: list[dict[str, Any]] = []
    _scores_csv = scores_csv if scores_csv is not None else SCORES_OUTPUT

    _clear_scoring_audit_cache(audit_dir=audit_dir)

    for entity in target_entities:
        layer = str(entity["layer"])
        applicable_topics = _get_applicable_topics(layer)

        positive_count = 0
        negative_count = 0
        topic_counts: dict[str, int] = {}
        top_positive_topic = ""
        top_positive_count = 0
        top_negative_topic = ""
        top_negative_count = 0
        entity_slug = sanitize_filename(str(entity["name"]))

        for topic in applicable_topics:
            result = _load_raw_result(entity, topic, raw_dir=raw_dir)
            topic_name = str(topic["topic_name"])
            polarity = str(topic["polarity"])
            topic_slug = sanitize_filename(topic_name)

            if result:
                aligned = scoring_aligned_results(result)
                count = len(aligned)
                _write_scoring_audit(
                    entity_slug,
                    topic_slug,
                    str(entity["name"]),
                    topic_name,
                    polarity,
                    aligned,
                    audit_dir=audit_dir,
                )
            else:
                count = 0

            topic_counts[topic_name] = count

            if polarity == "positive":
                positive_count += count
                if count > top_positive_count:
                    top_positive_count = count
                    top_positive_topic = topic_name
            else:
                negative_count += count
                if count > top_negative_count:
                    top_negative_count = count
                    top_negative_topic = topic_name

        terms_power_score = (
            positive_count / (positive_count + negative_count + 1) * 100
        )
        stress_score = 100 - terms_power_score

        row: dict[str, Any] = {
            "entity_name": entity["name"],
            "layer": layer,
            "ticker": entity["ticker"],
            "positive_count": positive_count,
            "negative_count": negative_count,
            "terms_power_score": round(terms_power_score, 2),
            "stress_score": round(stress_score, 2),
            "top_positive_topic": top_positive_topic,
            "top_negative_topic": top_negative_topic,
        }
        row.update(topic_counts)
        rows.append(row)

    df = pd.DataFrame(rows)

    _scores_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(_scores_csv, index=False)
    logger.info("Scores written to %s", _scores_csv)

    console.rule("[bold cyan]Scoring Summary")
    for layer_name in ("lender", "borrower", "bank"):
        layer_df = df[df["layer"] == layer_name].copy()
        if layer_df.empty:
            continue

        if layer_name == "lender":
            layer_df = layer_df.sort_values("terms_power_score", ascending=False)
            console.print("\n[bold]Lender Ranking[/bold] (by Terms Power Score):")
        elif layer_name == "borrower":
            layer_df = layer_df.sort_values("stress_score", ascending=False)
            console.print("\n[bold]Borrower Distress[/bold] (by Stress Score):")
        else:
            _g = layer_df["bank_market_share_gain"].fillna(0) if "bank_market_share_gain" in layer_df.columns else 0
            _p = layer_df["bank_credit_pullback"].fillna(0) if "bank_credit_pullback" in layer_df.columns else 0
            layer_df["net_position"] = _g - _p
            layer_df = layer_df.sort_values("net_position", ascending=False)
            console.print("\n[bold]Bank Contagion[/bold] (by Net Position):")

        for _, row_data in layer_df.iterrows():
            score_col = (
                "terms_power_score"
                if layer_name == "lender"
                else "stress_score"
                if layer_name == "borrower"
                else "net_position"
            )
            score_val = row_data.get(score_col, "N/A")
            console.print(
                f"  {row_data['entity_name']:<30} {score_col}={score_val}"
            )

    return df


if __name__ == "__main__":
    compute_scores()
