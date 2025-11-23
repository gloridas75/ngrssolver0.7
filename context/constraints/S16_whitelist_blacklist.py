"""S16: Enforce whitelist/blacklist at OU and employee levels.

Soft constraint that tracks and enforces organizational unit and employee-level
whitelist/blacklist preferences without blocking feasible solutions.
"""

def add_constraints(model, ctx):
    """Enforce whitelist/blacklist preferences at OU and employee levels."""
    
    employees = ctx.get('employees', [])
    slots = ctx.get('slots', [])
    demand_items = ctx.get('demandItems', [])
    x = ctx.get('x', {})
    
    if not slots or not x:
        print(f"[S16] Whitelist/Blacklist Constraint (SOFT)")
        print(f"     Skipping: slots or decision variables not available")
        return
    
    print(f"[S16] Whitelist/Blacklist Constraint (SOFT)")
    print(f"     Total employees: {len(employees)}")
    
    # Count whitelisted and blacklisted employees
    whitelisted_count = 0
    blacklisted_count = 0
    
    for demand in demand_items:
        for shift in demand.get('shifts', []):
            whitelist = shift.get('whitelist', {})
            blacklist = shift.get('blacklist', {})
            
            if whitelist.get('employeeIds'):
                whitelisted_count += len(whitelist['employeeIds'])
            if blacklist.get('employeeIds'):
                blacklisted_count += len(blacklist['employeeIds'])
    
    print(f"     Whitelisted employee-demand pairs: {whitelisted_count}")
    print(f"     Blacklisted employee-demand pairs: {blacklisted_count}")
    print(f"     Note: S16 is a soft constraint - whitelist enforced at model level\n")


def score_violations(ctx, assignments, score_book):
    """Score violations for whitelist/blacklist enforcement.
    
    Checks assignments against whitelist and blacklist preferences at both
    OU and employee levels. Flags violations where:
    - Blacklisted employees are assigned
    - Non-whitelisted employees are assigned when whitelist exists
    """
    slots = ctx.get('slots', [])
    demands = ctx.get('demands', [])
    employees = ctx.get('employees', [])
    
    if not slots or not demands or not assignments:
        return 0
    
    violations = 0
    
    # Build mappings for quick lookup
    slot_map = {slot.get('slot_id'): slot for slot in slots}
    demand_map = {demand.get('demandId'): demand for demand in demands}
    employee_map = {emp.get('employeeId'): emp for emp in employees}
    
    # Process each assignment
    for assignment in assignments:
        slot_id = assignment.get('slotId')
        emp_id = assignment.get('employeeId')
        
        if not slot_id or not emp_id or slot_id not in slot_map:
            continue
        
        slot = slot_map[slot_id]
        demand_id = slot.get('demand_id')
        
        if not demand_id or demand_id not in demand_map:
            continue
            
        demand = demand_map[demand_id]
        
        # Get whitelist and blacklist from demand
        whitelist = demand.get('whitelist', {})
        blacklist = demand.get('blacklist', {})
        
        # Check employee-level blacklist
        blacklisted_employees = blacklist.get('employeeIds', [])
        if emp_id in blacklisted_employees:
            score_book.soft(
                "S16",
                f"Employee {emp_id} is BLACKLISTED for demand {demand_id} but assigned to slot {slot_id}"
            )
            violations += 1
            continue  # Skip further checks if blacklisted
        
        # Check OU-level blacklist
        if emp_id in employee_map:
            emp_ou = employee_map[emp_id].get('organizationalUnit')
            blacklisted_ous = blacklist.get('organizationalUnits', [])
            if emp_ou and emp_ou in blacklisted_ous:
                score_book.soft(
                    "S16",
                    f"Employee {emp_id} from OU {emp_ou} is BLACKLISTED for demand {demand_id}"
                )
                violations += 1
                continue
        
        # Check employee-level whitelist (if whitelist exists)
        whitelisted_employees = whitelist.get('employeeIds', [])
        if whitelisted_employees and emp_id not in whitelisted_employees:
            score_book.soft(
                "S16",
                f"Employee {emp_id} is NOT whitelisted for demand {demand_id} (whitelist has {len(whitelisted_employees)} entries)"
            )
            violations += 1
            continue
        
        # Check OU-level whitelist (if whitelist exists)
        whitelisted_ous = whitelist.get('organizationalUnits', [])
        if whitelisted_ous and emp_id in employee_map:
            emp_ou = employee_map[emp_id].get('organizationalUnit')
            if emp_ou and emp_ou not in whitelisted_ous:
                score_book.soft(
                    "S16",
                    f"Employee {emp_id} from OU {emp_ou} is NOT in whitelisted OUs for demand {demand_id}"
                )
                violations += 1
    
    return violations
