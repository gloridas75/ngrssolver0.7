"""S8: Maintain target team strength by site/day (SOFT constraint).

Soft constraint that encourages achieving target team sizes per demand/site/day.
Violations occur when actual assigned headcount differs from target headcount.

This is typically handled by hard headcount constraints, but S8 provides soft
guidance for preferred team sizes beyond the strict minimum.
"""

from collections import defaultdict


def add_constraints(model, ctx):
    """
    S8 is a SOFT constraint - no model.Add() calls.
    
    Scoring happens post-solution via score_violations().
    """
    print(f"[S8] Team Size Feasibility (SOFT) - registered for post-solution scoring\n")


def score_violations(ctx, assignments, score_book):
    """
    Calculate S8 team size violations.
    
    For each slot, check if the assigned headcount matches the target.
    This is typically enforced by hard constraints (headcount = exactly N),
    but S8 can flag preferred team sizes or skill diversity issues.
    
    Current implementation: Check if we have sufficient skill diversity
    in each demand's assignments on each day.
    
    Args:
        ctx: Context dict with employees, demand_items, slots
        assignments: List of assignment dicts from solver
        score_book: ScoreBook instance for recording violations
    
    Returns:
        Number of violations detected
    """
    
    employees = ctx.get('employees', [])
    demand_items = ctx.get('demandItems', [])
    slots = ctx.get('slots', [])
    
    # Build employee skills map
    emp_skills = {}
    for emp in employees:
        emp_id = emp.get('employeeId')
        skills = emp.get('skills', [])
        skill_list = []
        for skill in skills:
            if isinstance(skill, dict):
                skill_list.append(skill.get('skillId', 'UNKNOWN'))
            else:
                skill_list.append(str(skill))
        emp_skills[emp_id] = set(skill_list)
    
    # Build demand required skills
    demand_required_skills = {}
    for demand in demand_items:
        demand_id = demand.get('demandId')
        required_skills = set()
        for shift in demand.get('shifts', []):
            skills = shift.get('requiredSkills', [])
            required_skills.update(skills)
        if required_skills:
            demand_required_skills[demand_id] = required_skills
    
    # Group assignments by (demand, date)
    demand_date_assignments = defaultdict(list)
    for assignment in assignments:
        demand_id = assignment.get('demandId')
        date_str = assignment.get('date')
        if demand_id and date_str:
            demand_date_assignments[(demand_id, date_str)].append(assignment)
    
    violations = 0
    
    # Check each demand-date for skill coverage
    for (demand_id, date_str), day_assignments in demand_date_assignments.items():
        required_skills = demand_required_skills.get(demand_id, set())
        
        if not required_skills:
            continue
        
        # Collect all skills present in this day's team
        team_skills = set()
        for assignment in day_assignments:
            emp_id = assignment.get('employeeId')
            if emp_id in emp_skills:
                team_skills.update(emp_skills[emp_id])
        
        # Check if all required skills are covered
        missing_skills = required_skills - team_skills
        
        if missing_skills:
            for skill in missing_skills:
                score_book.soft(
                    "S8",
                    f"Demand {demand_id} on {date_str}: missing required skill {skill} in team"
                )
                violations += 1
    
    return violations
