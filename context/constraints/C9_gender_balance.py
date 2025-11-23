"""C9: Gender balance for sensitive roles (HARD constraint).

Enforce gender mix requirements for frisking/screening roles.
Example: Minimum 1 female required for frisking duty.

Input Schema (v0.70):
- Slot objects have genderRequirement from requirements ('Any', 'M', 'F', 'Mix')
"""
from collections import defaultdict


def add_constraints(model, ctx):
    """
    Enforce gender balance requirements for sensitive roles (HARD).
    
    Strategy: For each slot with gender requirements, ensure appropriate gender assignment.
    v0.70: genderRequirement is directly on slot from requirement.
    
    Args:
        model: CP-SAT model
        ctx: Context dict with 'slots', 'employees', 'x'
    """
    
    slots = ctx.get('slots', [])
    employees = ctx.get('employees', [])
    x = ctx.get('x', {})
    
    if not slots or not x or not employees:
        print(f"[C9] Warning: Slots, employees, or decision variables not available")
        return
    
    # Build employee gender map
    emp_gender = {}  # emp_id -> 'M' or 'F'
    for emp in employees:
        emp_id = emp.get('employeeId')
        gender = emp.get('gender', 'U')  # U = Unknown
        emp_gender[emp_id] = gender
    
    constraints_added = 0
    mix_constraints_added = 0
    
    # Group slots by (date, demandId, requirementId) for Mix enforcement
    # This allows us to enforce gender mix across all slots on the same date/requirement
    slots_by_group = defaultdict(list)
    for slot in slots:
        gender_req = getattr(slot, 'genderRequirement', 'Any')
        if gender_req == 'Mix':
            # Group by date and requirement to enforce mix across daily headcount
            group_key = (slot.date, slot.demandId, slot.requirementId)
            slots_by_group[group_key].append(slot)
    
    # For each slot with gender requirements, add constraints
    # v0.70: genderRequirement is directly on slot
    for slot in slots:
        gender_req = getattr(slot, 'genderRequirement', 'Any')
        
        # For simple requirements: 'M' (male only), 'F' (female only)
        if gender_req == 'M':
            # Only male employees can be assigned
            for emp in employees:
                emp_id = emp.get('employeeId')
                if emp_gender.get(emp_id) != 'M' and (slot.slot_id, emp_id) in x:
                    var = x[(slot.slot_id, emp_id)]
                    model.Add(var == 0)
                    constraints_added += 1
        elif gender_req == 'F':
            # Only female employees can be assigned
            for emp in employees:
                emp_id = emp.get('employeeId')
                if emp_gender.get(emp_id) != 'F' and (slot.slot_id, emp_id) in x:
                    var = x[(slot.slot_id, emp_id)]
                    model.Add(var == 0)
                    constraints_added += 1
    
    # Enforce 'Mix' requirement: At least 1 male AND 1 female per group
    for group_key, group_slots in slots_by_group.items():
        date, demand_id, req_id = group_key
        
        # Skip if only 1 slot in group (can't have mix with headcount=1)
        if len(group_slots) < 2:
            continue
        
        # Collect all male and female assignment variables for this group
        male_vars = []
        female_vars = []
        
        for slot in group_slots:
            for emp in employees:
                emp_id = emp.get('employeeId')
                if (slot.slot_id, emp_id) in x:
                    var = x[(slot.slot_id, emp_id)]
                    if emp_gender.get(emp_id) == 'M':
                        male_vars.append(var)
                    elif emp_gender.get(emp_id) == 'F':
                        female_vars.append(var)
        
        # Add constraints: At least 1 male AND at least 1 female must be assigned
        if male_vars and female_vars:
            # At least 1 male: sum(male_vars) >= 1
            model.Add(sum(male_vars) >= 1)
            mix_constraints_added += 1
            
            # At least 1 female: sum(female_vars) >= 1
            model.Add(sum(female_vars) >= 1)
            mix_constraints_added += 1
    
    # Count slots with gender requirements
    gender_req_slots = sum(1 for s in slots if getattr(s, 'genderRequirement', 'Any') != 'Any')
    mix_groups = len(slots_by_group)
    
    # Count employees by gender
    male_count = sum(1 for e in employees if emp_gender.get(e.get('employeeId')) == 'M')
    female_count = sum(1 for e in employees if emp_gender.get(e.get('employeeId')) == 'F')
    
    print(f"[C9] Gender Balance Constraint (HARD)")
    print(f"     Total employees: {len(employees)}")
    print(f"     Male officers: {male_count}, Female officers: {female_count}")
    print(f"     Slots with gender requirements: {gender_req_slots}")
    print(f"     ✓ Added {constraints_added} M/F filter constraints")
    print(f"     ✓ Added {mix_constraints_added} Mix enforcement constraints ({mix_groups} groups)\n")
