#!/usr/bin/env python3
"""Rebuild a single Node-RED flows.json from the split files in node-red/.

    python3 tools/nodered_build.py > .export/flows.json

Import the result in Node-RED (☰ › Import › select file › "Import" with
"Replace" for existing nodes), or import a single tab file from node-red/flows/.
Credentials (tokens, passwords, the alarm code) are not in this repo and must be
re-entered after a restore onto a fresh Node-RED.
"""
import json
from pathlib import Path

NR = Path(__file__).resolve().parent.parent / "node-red"


def build() -> list:
    idx = json.loads((NR / "index.json").read_text(encoding="utf-8"))
    out = json.loads((NR / idx["config_nodes"]).read_text(encoding="utf-8"))
    for item in idx["subflows"] + idx["tabs"]:
        out += json.loads((NR / item["file"]).read_text(encoding="utf-8"))
    return out


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False))
