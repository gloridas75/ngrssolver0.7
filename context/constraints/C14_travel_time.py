"""C14: Apply travel time constraints between site assignments (HARD).

Enforce minimum travel time between consecutive shifts at different sites.
If an employee works at Site A and then Site B on the same day, there must be
sufficient time for travel between sites.

Default travel time: 30 minutes between different sites.
Same site: no travel time needed.
"""

from datetime import timedelta


def add_constraints(model, ctx):
    """
    Enforce travel time between consecutive shifts at different sites (HARD).
    
    Strategy: For each employee, identify consecutive shifts at different sites.
    If travel time is insufficient, add disjunctive constraint.
    
    Args:
        model: CP-SAT model
        ctx: Context dict with 'slots', 'employees', 'x'
    """
    
    slots = ctx.get('slots', [])
    employees = ctx.get('employees', [])
    x = ctx.get('x', {})
    
    if not slots or not x or not employees:
        print(f"[C14] Travel Time Between Sites Constraint (HARD)")
        print(f"     Skipping: slots or decision variables not available\n")
        return
    
    # Default travel time: 30 minutes
    travel_time_minutes = 30
    travel_time_delta = timedelta(minutes=travel_time_minutes)
    
    constraints_added = 0
    
    # For each employee, check consecutive shifts for travel conflicts
    for emp in employees:
        emp_id = emp.get('employeeId')
        
        # Get all slots this employee could be assigned to
        emp_slots = [s for s in slots if (s.slot_id, emp_id) in x]
        
        if len(emp_slots) < 2:
            continue
        
        # Sort by date and start time
        sorted_slots = sorted(emp_slots, key=lambda s: (s.date, s.start))
        
        # Check consecutive pairs on the same day
        for i in range(len(sorted_slots) - 1):
            slot1 = sorted_slots[i]
            slot2 = sorted_slots[i + 1]
            
            # Only check if same day and different sites
            if slot1.date != slot2.date:
                continue
            
            if slot1.siteId == slot2.siteId:
                continue  # Same site, no travel needed
            
            # Different sites on same day; check travel time
            travel_available = slot2.start - slot1.end
            
            if travel_available < travel_time_delta:
                # Insufficient travel time
                var1 = x[(slot1.slot_id, emp_id)]
                var2 = x[(slot2.slot_id, emp_id)]
                
                # Constraint: NOT (var1 AND var2)
                model.Add(var1 + var2 <= 1)
                constraints_added += 1
    
    print(f"[C14] Travel Time Between Sites Constraint (HARD)")
    print(f"     Employees: {len(employees)}, Slots: {len(slots)}")
    print(f"     Travel time required: {travel_time_minutes} minutes between different sites")
    print(f"     ✓ Added {constraints_added} travel time disjunctive constraints\n")
