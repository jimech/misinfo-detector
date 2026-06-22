"""
corpus.py
----------
Loads the static evidence corpus from data/evidence.json into
a list of Evidence objects (the shape defined in schemas.py).

Keeping loading in its own file means later we could swap the
JSON file for a database or a live search API, and nothing else
in the pipeline has to change.
"""

import json
from pathlib import Path
from src.schemas import Evidence

# Build a path to data/evidence.json that works no matter where
# the program is run from. We go up from this file (src/) to the
# project root, then into data/.
_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "evidence.json"


def load_evidence() -> list[Evidence]:
    """Read evidence.json and return a list of Evidence objects."""
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    evidence_list = [
        Evidence(source_title=item["source_title"], text=item["text"])
        for item in raw
    ]
    return evidence_list