"""C10: Employee must have all required skills for shift (HARD constraint).

Enforce strict skill matching: no employee can be assigned to a shift
without possessing all required skills.

Input Schema (v0.70):
- Slot objects may have requiredSkills from requirements (if applicable)
"""
from collections import defaultdict


def add_constraints(model, ctx):
    """
    Enforce skill/role matching (HARD).
    
    Strategy: For each slot, identify required skills.
    For each employee lacking any required skill, block assignment.
    v0.70: Skills would be in slot properties if defined in requirements.
    
    Args:
        model: CP-SAT model
        ctx: Context dict with 'slots', 'employees', 'x'
    """
    
    slots = ctx.get('slots', [])
    employees = ctx.get('employees', [])
    x = ctx.get('x', {})
    
    if not slots or not x or not employees:
        print(f"[C10] Warning: Slots, employees, or decision variables not available")
        return
    
    # Build employee skills map
    emp_skills = {}  # emp_id -> set of skills
    for emp in employees:
        emp_id = emp.get('employeeId')
        skills = set(emp.get('skills', []))
        emp_skills[emp_id] = skills
    
    # v0.70: Check if slots have requiredSkills property
    # Note: Current schema uses requiredQualifications, not requiredSkills
    # This constraint may not be needed for current schema
    constraints_added = 0
    slots_with_skill_reqs = 0
    
    for slot in slots:
        # Check for requiredSkills attribute (may not exist in current schema)
        required_skills = set(getattr(slot, 'requiredSkills', []))
        
        if not required_skills:
            continue
        
        slots_with_skill_reqs += 1
        
        # For each employee, check if they have all required skills
        for emp in employees:
            emp_id = emp.get('employeeId')
            emp_sks = emp_skills.get(emp_id, set())
            
            if (slot.slot_id, emp_id) not in x:
                continue
            
            # Check if employee has all required skills
            if not required_skills.issubset(emp_sks):
                # Employee missing some required skills - block assignment
                var = x[(slot.slot_id, emp_id)]
                model.Add(var == 0)
                constraints_added += 1
    
    # Collect statistics
    all_skills = set()
    for emp in employees:
        all_skills.update(emp.get('skills', []))
    
    print(f"[C10] Skill/Role Match Constraint (HARD)")
    print(f"     Employees: {len(employees)}, Unique skills: {len(all_skills)}")
    print(f"     Slots with skill requirements: {slots_with_skill_reqs}")
    print(f"     ✓ Added {constraints_added} skill mismatch constraints\n")
