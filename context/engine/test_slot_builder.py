#!/usr/bin/env python3
"""Quick test to verify slot_builder functionality."""

import sys
import pathlib
import json

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from context.engine.slot_builder import build_slots, print_slots
from context.engine.data_loader import load_input

def test_slot_builder():
    """Test slot builder with sample input."""
    print("=" * 80)
    print("SLOT BUILDER TEST")
    print("=" * 80)
    
    # Load input
    ctx = load_input("input.json")
    
    # Build slots
    slots = build_slots(ctx)
    
    # Print slot details
    print_slots(slots, limit=10)
    
    # Summary
    print(f"\n[Summary]")
    print(f"  Total slots created: {len(slots)}")
    
    # Group by demand
    by_demand = {}
    for slot in slots:
        if slot.demandId not in by_demand:
            by_demand[slot.demandId] = []
        by_demand[slot.demandId].append(slot)
    
    for demand_id, demand_slots in by_demand.items():
        print(f"  {demand_id}: {len(demand_slots)} slots")
    
    # Group by shift code
    by_code = {}
    for slot in slots:
        if slot.shiftCode not in by_code:
            by_code[slot.shiftCode] = 0
        by_code[slot.shiftCode] += 1
    
    print(f"\n  Slots by shift code:")
    for code, count in sorted(by_code.items()):
        print(f"    {code}: {count}")
    
    print("\n✓ Test complete!")

if __name__ == "__main__":
    test_slot_builder()
