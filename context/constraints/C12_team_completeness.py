"""C12: Team completeness - all required team members present (HARD constraint).

For team-based shifts, all assigned employees must be from the same preferred team(s).
Ensures team cohesion and roster integrity.
"""


def add_constraints(model, ctx):
    """
    Enforce team completeness: all assignments from same team (HARD).
    
    Strategy: For each slot with preferredTeams defined, block employees not in those teams.
    
    Args:
        model: CP-SAT model
        ctx: Context dict with 'slots', 'employees', 'x'
    """
    slots = ctx.get('slots', [])
    employees = ctx.get('employees', [])
    x = ctx.get('x', {})
    
    if not slots or not x or not employees:
        print(f"[C12] Warning: Slots, employees, or decision variables not available")
        return
    
    # Build employee team map
    emp_teams = {emp.get('employeeId'): emp.get('teamId') for emp in employees}
    
    constraints_added = 0
    slots_with_teams = 0
    
    # For each slot with team preferences, block non-team employees
    for slot in slots:
        if slot.preferredTeams:
            slots_with_teams += 1
            for emp in employees:
                emp_id = emp.get('employeeId')
                emp_team = emp_teams.get(emp_id)
                
                if (slot.slot_id, emp_id) not in x:
                    continue
                
                # If employee's team not in preferred teams, block assignment
                if emp_team not in slot.preferredTeams:
                    var = x[(slot.slot_id, emp_id)]
                    model.Add(var == 0)
                    constraints_added += 1
    
    print(f"[C12] Team Completeness Constraint (HARD)")
    print(f"     Total slots: {len(slots)}")
    print(f"     Slots with team preferences: {slots_with_teams}")
    print(f"     ✓ Added {constraints_added} team membership constraints\n")
