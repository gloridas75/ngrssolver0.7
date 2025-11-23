"""C4: Minimum 8h rest between shifts (HARD constraint).

Enforce minimum rest period between consecutive shifts for the same employee.
Default: 8 hours = 480 minutes minimum rest between shift end and next shift start.
"""
from collections import defaultdict
from datetime import timedelta


def add_constraints(model, ctx):
    """
    Enforce minimum rest period between consecutive shifts (HARD).
    
    Strategy: For each employee, identify shift pairs that violate the min rest requirement.
    Add disjunctive constraints: NOT (both shifts assigned).
    
    Args:
        model: CP-SAT model
        ctx: Context dict with 'slots', 'employees', 'x', 'constraintList'
    """
    
    slots = ctx.get('slots', [])
    employees = ctx.get('employees', [])
    x = ctx.get('x', {})
    constraint_list = ctx.get('constraintList', [])
    
    if not slots or not x or not employees:
        print(f"[C4] Warning: Slots, employees, or decision variables not available")
        return
    
    # Extract min rest requirement from constraint config
    min_rest_minutes = 480  # Default: 8 hours
    for constraint in constraint_list:
        if constraint.get('id') == 'apgdMinRestBetweenShifts':
            min_rest_minutes = constraint.get('params', {}).get('minRestMinutes', 480)
            break
    
    min_rest_delta = timedelta(minutes=min_rest_minutes)
    
    constraints_added = 0
    
    # For each employee, check all shift pairs
    for emp in employees:
        emp_id = emp.get('employeeId')
        
        # Get all slots this employee could be assigned to
        emp_slots = [s for s in slots if (s.slot_id, emp_id) in x]
        
        if len(emp_slots) < 2:
            continue
        
        # Sort by end time (date + end datetime)
        sorted_slots = sorted(emp_slots, key=lambda s: (s.date, s.end))
        
        # Check ALL pairs where slot1 ends before slot2 starts
        # and there's insufficient rest between them
        for i in range(len(sorted_slots)):
            slot1 = sorted_slots[i]
            
            # Check all subsequent slots that might violate rest period
            for j in range(i + 1, len(sorted_slots)):
                slot2 = sorted_slots[j]
                
                # Skip if slot2 starts before slot1 ends (impossible overlap)
                if slot2.start < slot1.end:
                    continue
                
                # Calculate rest time between slot1 end and slot2 start
                rest_available = slot2.start - slot1.end
                
                # If rest is insufficient, add disjunctive constraint
                if rest_available < min_rest_delta:
                    var1 = x[(slot1.slot_id, emp_id)]
                    var2 = x[(slot2.slot_id, emp_id)]
                    
                    # Constraint: NOT (var1 AND var2)
                    # Implemented as: var1 + var2 <= 1
                    model.Add(var1 + var2 <= 1)
                    constraints_added += 1
                else:
                    # Once we find a slot with sufficient rest, all later slots will too
                    # (since sorted by end time, and checking chronologically)
                    break
    
    print(f"[C4] Minimum Rest Between Shifts Constraint (HARD)")
    print(f"     Employees: {len(employees)}, Slots: {len(slots)}")
    print(f"     Minimum rest required: {min_rest_minutes} minutes ({min_rest_minutes/60:.1f}h)")
    print(f"     ✓ Added {constraints_added} rest period disjunctive constraints\n")
