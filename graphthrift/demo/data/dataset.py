"""Demo corpus: an agent-memory conversation stream (Graphiti's core use case).

Design choices that make the demo meaningful:
- Restated facts across episodes (e.g. Alice works at Acme, mentioned again later)
  -> the dedup prefilter and response cache have real work to eliminate.
- salience<0.5 entities and hard=True edges -> the SMALL model (aggressive router)
  misses them, so routing carries a measurable quality cost.
- elusive=True items are in the gold graph but even the MEDIUM model misses them,
  so the baseline F1 is realistically < 1.0.
"""
from __future__ import annotations

from typing import Any

EPISODES: list[dict[str, Any]] = [
    {
        "id": "ep01",
        "text": "Alice joined Acme Corp as a staff engineer in January and started leading the Atlas project.",
        "entities": [
            {"name": "Alice", "type": "Person", "salience": 0.95},
            {"name": "Acme Corp", "type": "Organization", "salience": 0.9},
            {"name": "Atlas", "type": "Project", "salience": 0.8},
            {"name": "January", "type": "Date", "salience": 0.3},
        ],
        "triples": [
            {"subject": "Alice", "predicate": "WORKS_AT", "object": "Acme Corp", "valid_at": "2024-01-15"},
            {"subject": "Alice", "predicate": "LEADS", "object": "Atlas", "valid_at": "2024-01-20"},
        ],
    },
    {
        "id": "ep02",
        "text": "Bob is a data scientist at Acme Corp who reports to Alice and prefers working in Python.",
        "entities": [
            {"name": "Bob", "type": "Person", "salience": 0.95},
            {"name": "Acme Corp", "type": "Organization", "salience": 0.9},
            {"name": "Alice", "type": "Person", "salience": 0.9},
            {"name": "Python", "type": "Skill", "salience": 0.45},
        ],
        "triples": [
            {"subject": "Bob", "predicate": "WORKS_AT", "object": "Acme Corp", "valid_at": "2024-02-01"},
            {"subject": "Bob", "predicate": "REPORTS_TO", "object": "Alice", "valid_at": "2024-02-01"},
            {"subject": "Bob", "predicate": "PREFERS", "object": "Python", "hard": True, "valid_at": "2024-02-01"},
        ],
    },
    {
        "id": "ep03",
        "text": "The Atlas project uses a Postgres database and depends on the Helios internal service.",
        "entities": [
            {"name": "Atlas", "type": "Project", "salience": 0.85},
            {"name": "Postgres", "type": "Technology", "salience": 0.6},
            {"name": "Helios", "type": "Service", "salience": 0.55},
        ],
        "triples": [
            {"subject": "Atlas", "predicate": "USES", "object": "Postgres", "valid_at": "2024-02-10"},
            {"subject": "Atlas", "predicate": "DEPENDS_ON", "object": "Helios", "hard": True, "valid_at": "2024-02-10"},
        ],
    },
    {
        "id": "ep04",
        "text": "Alice works at Acme Corp and mentioned the Atlas launch is targeted for June.",
        "entities": [
            {"name": "Alice", "type": "Person", "salience": 0.9},
            {"name": "Acme Corp", "type": "Organization", "salience": 0.9},
            {"name": "Atlas", "type": "Project", "salience": 0.85},
            {"name": "June", "type": "Date", "salience": 0.3},
        ],
        # 'Alice WORKS_AT Acme Corp' is a RESTATED fact from ep01 -> prefilter/cache win
        "triples": [
            {"subject": "Alice", "predicate": "WORKS_AT", "object": "Acme Corp", "valid_at": "2024-01-15"},
            {"subject": "Atlas", "predicate": "LAUNCHES_IN", "object": "June", "valid_at": "2024-06-01"},
        ],
    },
    {
        "id": "ep05",
        "text": "Carol from Globex partnered with Acme Corp on the Atlas integration and knows Alice well.",
        "entities": [
            {"name": "Carol", "type": "Person", "salience": 0.9},
            {"name": "Globex", "type": "Organization", "salience": 0.85},
            {"name": "Acme Corp", "type": "Organization", "salience": 0.9},
            {"name": "Atlas", "type": "Project", "salience": 0.8},
            {"name": "Alice", "type": "Person", "salience": 0.85},
        ],
        "triples": [
            {"subject": "Carol", "predicate": "WORKS_AT", "object": "Globex", "valid_at": "2024-03-01"},
            {"subject": "Globex", "predicate": "PARTNERS_WITH", "object": "Acme Corp", "valid_at": "2024-03-05"},
            {"subject": "Carol", "predicate": "KNOWS", "object": "Alice", "elusive": True, "valid_at": "2024-03-05"},
        ],
    },
    {
        "id": "ep06",
        "text": "Bob works at Acme Corp and is now also contributing to the Helios service maintenance.",
        "entities": [
            {"name": "Bob", "type": "Person", "salience": 0.9},
            {"name": "Acme Corp", "type": "Organization", "salience": 0.9},
            {"name": "Helios", "type": "Service", "salience": 0.55},
        ],
        # 'Bob WORKS_AT Acme Corp' restated from ep02
        "triples": [
            {"subject": "Bob", "predicate": "WORKS_AT", "object": "Acme Corp", "valid_at": "2024-02-01"},
            {"subject": "Bob", "predicate": "CONTRIBUTES_TO", "object": "Helios", "hard": True, "valid_at": "2024-04-01"},
        ],
    },
    {
        "id": "ep07",
        "text": "Alice leads Atlas and set up a weekly sync with Carol to track the integration.",
        "entities": [
            {"name": "Alice", "type": "Person", "salience": 0.9},
            {"name": "Atlas", "type": "Project", "salience": 0.85},
            {"name": "Carol", "type": "Person", "salience": 0.85},
        ],
        # 'Alice LEADS Atlas' restated from ep01
        "triples": [
            {"subject": "Alice", "predicate": "LEADS", "object": "Atlas", "valid_at": "2024-01-20"},
            {"subject": "Alice", "predicate": "SYNCS_WITH", "object": "Carol", "elusive": True, "valid_at": "2024-04-10"},
        ],
    },
    {
        "id": "ep08",
        "text": "The Helios service is written in Go and uses Postgres for storage, maintained by Bob.",
        "entities": [
            {"name": "Helios", "type": "Service", "salience": 0.6},
            {"name": "Go", "type": "Technology", "salience": 0.5},
            {"name": "Postgres", "type": "Technology", "salience": 0.6},
            {"name": "Bob", "type": "Person", "salience": 0.85},
        ],
        "triples": [
            {"subject": "Helios", "predicate": "USES", "object": "Go", "hard": True, "valid_at": "2024-04-15"},
            {"subject": "Helios", "predicate": "USES", "object": "Postgres", "valid_at": "2024-04-15"},
        ],
    },
]


def gold_graph() -> dict[str, Any]:
    """Ground-truth graph = deduped union of every annotated entity and triple."""
    ents: dict[str, dict[str, Any]] = {}
    trs: dict[tuple[str, str, str], dict[str, Any]] = {}
    for ep in EPISODES:
        for e in ep["entities"]:
            ents.setdefault(e["name"].lower(), {"name": e["name"], "type": e["type"]})
        for t in ep["triples"]:
            k = (t["subject"].lower(), t["predicate"].lower(), t["object"].lower())
            trs.setdefault(k, {"subject": t["subject"], "predicate": t["predicate"], "object": t["object"]})
    return {"entities": list(ents.values()), "triples": list(trs.values())}
