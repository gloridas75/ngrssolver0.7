"""S4: Penalize short gaps < 8h between shifts (SOFT constraint).

Soft constraint that discourages gaps shorter than 8 hours between consecutive shifts.
Unlike C4 (hard constraint), this allows violations for feasibility but scores them.

Encourages better employee rest and work-life balance.
"""

from datetime import datetime, timedelta


def add_constraints(model, ctx):
    """
    S4 is a SOFT constraint - no model.Add() calls.
    
    Scoring happens post-solution via score_violations().
    """
    print(f"[S4] Minimize Short Rest Gaps (SOFT) - registered for post-solution scoring\n")


def score_violations(ctx, assignments, score_book):
    """
    Calculate S4 short rest gap violations.
    
    For each employee, check all consecutive shift pairs. If the gap between
    shift end and next shift start is less than 8 hours (480 minutes), record violation.
    
    Args:
        ctx: Context dict
        assignments: List of assignment dicts from solver
        score_book: ScoreBook instance for recording violations
    
    Returns:
        Number of violations detected
    """
    
    from collections import defaultdict
    
    # Get min rest configuration
    constraint_list = ctx.get('constraintList', [])
    min_rest_minutes = 480  # Default: 8 hours
    
    for constraint in constraint_list:
        if constraint.get('id') == 'apgdMinRestBetweenShifts':
            min_rest_minutes = constraint.get('params', {}).get('minRestMinutes', 480)
            break
    
    min_rest_delta = timedelta(minutes=min_rest_minutes)
    
    # Group assignments by employee
    emp_assignments = defaultdict(list)
    
    for assignment in assignments:
        emp_id = assignment.get('employeeId')
        if emp_id:
            emp_assignments[emp_id].append(assignment)
    
    violations = 0
    
    # Check each employee's assignment sequence
    for emp_id, assignments_list in emp_assignments.items():
        if len(assignments_list) < 2:
            continue
        
        # Sort by start time
        sorted_assignments = sorted(assignments_list, key=lambda a: a.get('startDateTime', ''))
        
        # Check consecutive pairs
        for i in range(len(sorted_assignments) - 1):
            a1 = sorted_assignments[i]
            a2 = sorted_assignments[i + 1]
            
            try:
                end1 = datetime.fromisoformat(a1.get('endDateTime'))
                start2 = datetime.fromisoformat(a2.get('startDateTime'))
                
                rest_gap = start2 - end1
                
                # If rest gap is less than minimum, record violation
                if rest_gap < min_rest_delta:
                    hours_gap = rest_gap.total_seconds() / 3600.0
                    score_book.soft(
                        "S4",
                        f"{emp_id}: rest gap {hours_gap:.1f}h between {a1.get('date')} and {a2.get('date')} is below {min_rest_minutes/60:.1f}h minimum"
                    )
                    violations += 1
            except:
                pass
    
    return violations
