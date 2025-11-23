#!/usr/bin/env python3
"""Debug script to check model validity."""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from context.engine.data_loader import load_input
from context.engine.solver_engine import build_model
from ortools.sat.python import cp_model

# Load input
ctx = load_input("input.json")

# Build model
model = build_model(ctx)

# Try to validate
print("\n[DEBUG] Model Status:", model.Proto())
print("\n[DEBUG] Attempting validation...")

solver = cp_model.CpSolver()
status = solver.Solve(model)

status_map = {
    0: "UNKNOWN",
    1: "OPTIMAL",
    2: "FEASIBLE",
    3: "INFEASIBLE",
    4: "MODEL_INVALID"
}

print(f"\n[DEBUG] Status Code: {status}")
print(f"[DEBUG] Status Name: {status_map.get(status, 'UNKNOWN')}")

# Check statistics
print(f"\n[DEBUG] Statistics:")
print(f"  Variables: {len(model.Proto().variables)}")
print(f"  Constraints: {len(model.Proto().constraints)}")
