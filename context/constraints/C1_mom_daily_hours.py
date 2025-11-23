"""C1: Daily hours cap by scheme (gross hours = normal + lunch, not OT).

HARD Constraint - enforced via model.Add():
- Scheme A: ≤ 14 hours per day (gross)
- Scheme B: ≤ 13 hours per day (gross)
- Scheme P: ≤ 9 hours per day (gross)

Note: Gross hours = total shift duration (includes lunch break).
For 44-hour weekly cap, see C2 (normal hours only).
For 72-hour monthly OT cap, see C17 (ot hours only).

Per-shift constraints: Each individual shift must not exceed scheme max.

Input Schema (v0.70):
- employees: [{ employeeId, scheme, ... }]
- Slot objects have start and end datetime fields
"""
from collections import defaultdict
from datetime import datetime, timedelta
from context.engine.time_utils import split_shift_hours


def add_constraints(model, ctx):
    """
    Enforce maximum daily gross working hours by employee scheme.
    
    HARD Constraint: Each shift must not exceed gross hours limit for employee's scheme.
    - Scheme A: ≤ 14 hours per shift
    - Scheme B: ≤ 13 hours per shift
    - Scheme P: ≤ 9 hours per shift
    
    Gross hours = total shift duration including lunch break.
    v0.70: Use slot.start and slot.end directly.
    
    Strategy: For each slot, check its gross hours against scheme limits.
    If any slot exceeds the limit for an employee's scheme, block assignment via model.Add(var == 0).
    
    Args:
        model: CP-SAT model
        ctx: Context dict with 'employees', 'slots', 'x'
    """
    
    employees = ctx.get('employees', [])
    slots = ctx.get('slots', [])
    x = ctx.get('x', {})
    
    if not slots or not x:
        print(f"[C1] Warning: Slots or decision variables not available")
        return
    
    # Build employee scheme map
    employee_scheme = {}
    for emp in employees:
        emp_id = emp.get('employeeId')
        scheme = emp.get('scheme', 'A')
        employee_scheme[emp_id] = scheme
    
    # Define max gross hours per scheme
    max_gross_by_scheme = {
        'A': 14.0,  # Scheme A: max 14 hours per day
        'B': 13.0,  # Scheme B: max 13 hours per day
        'P': 9.0    # Scheme P: max 9 hours per day
    }
    
    # Build shift hour map from slots
    shift_hours = {}  # (demandId, shiftCode) -> gross_hours
    for slot in slots:
        key = (slot.demandId, slot.shiftCode)
        if key not in shift_hours:
            gross = (slot.end - slot.start).total_seconds() / 3600.0
            shift_hours[key] = gross
    
    # Add constraints: For each slot-employee pair, check if shift exceeds scheme limit
    constraints_added = 0
    
    for slot in slots:
        slot_key = (slot.demandId, slot.shiftCode)
        gross_hours = shift_hours.get(slot_key, 0)
        
        for emp in employees:
            emp_id = emp.get('employeeId')
            
            if (slot.slot_id, emp_id) not in x:
                continue
            
            scheme = employee_scheme.get(emp_id, 'A')
            max_gross = max_gross_by_scheme.get(scheme, 14.0)
            
            # If shift exceeds scheme limit, block assignment
            if gross_hours > max_gross:
                var = x[(slot.slot_id, emp_id)]
                model.Add(var == 0)
                constraints_added += 1
    
    print(f"[C1] Daily Gross Hours Constraint (HARD - by Scheme)")
    print(f"     Total employees: {len(employees)}")
    print(f"     Total slots: {len(slots)}")
    print(f"     Unique shifts: {len(shift_hours)}")
    print(f"     Scheme limits: A≤{max_gross_by_scheme['A']}h, B≤{max_gross_by_scheme['B']}h, P≤{max_gross_by_scheme['P']}h")
    print(f"     ✓ Added {constraints_added} per-shift scheme violations blocks\n")
