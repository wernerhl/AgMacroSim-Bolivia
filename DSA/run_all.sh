#!/bin/zsh
# Reproduce the Bolivia MFMod-BOL DSA. Seed fixed in dsa_core.py (20260910).
# Gate first: do not proceed on a failed reproduction check.
set -e
cd "$(dirname "$0")"
echo "== Phase 1 gate (reproduction) =="; /usr/bin/python3 code/dsa_core.py > /tmp/dsa_gate.txt
grep -q "S0" /tmp/dsa_gate.txt || { echo "GATE FAILED"; exit 1; }
echo "== Phase 2-4 core scenarios =="; /usr/bin/python3 code/dsa_core.py
echo "== Phase 5-6 fan / bifurcation / sensitivity =="; /usr/bin/python3 code/dsa_analysis.py
echo "== exhibits =="; /usr/bin/python3 code/dsa_exhibits.py
echo "DONE. See outputs/ and exhibits/."
