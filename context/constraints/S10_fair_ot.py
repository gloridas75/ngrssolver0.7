"""S10: Balance OT fairly across eligible staff (SOFT constraint).

Soft constraint that encourages fair distribution of overtime hours across
eligible employees. Violations occur when OT distribution is unbalanced.

Strategy: Calculate OT for each employee, identify outliers (employees with
significantly more/less OT than average).
"""

from collections import defaultdict
from datetime import datetime


def add_constraints(model, ctx):
    """
    S10 is a SOFT constraint - no model.Add() calls.
    
    Scoring happens post-solution via score_violations().
    """
    print(f"[S10] Fair OT Distribution (SOFT) - registered for post-solution scoring\n")


def score_violations(ctx, assignments, score_book):
    """
    Calculate S10 fair OT distribution violations.
    
    For each employee, calculate total OT hours. Flag employees with significantly
    more OT than average (unfair burden) or significantly less (missed opportunity).
    
    Threshold: Employee OT > 1.5x average or < 0.5x average
    
    Args:
        ctx: Context dict with employees
        assignments: List of assignment dicts from solver
        score_book: ScoreBook instance for recording violations
    
    Returns:
        Number of violations detected
    """
    
    employees = ctx.get('employees', [])
    
    # Build employee scheme map
    emp_scheme = {}
    for emp in employees:
        emp_id = emp.get('employeeId')
        scheme = emp.get('scheme', 'A')
        emp_scheme[emp_id] = scheme
    
    # Calculate OT hours per employee
    emp_ot_hours = defaultdict(float)
    
    for assignment in assignments:
        emp_id = assignment.get('employeeId')
        
        try:
            start_dt = datetime.fromisoformat(assignment.get('startDateTime'))
            end_dt = datetime.fromisoformat(assignment.get('endDateTime'))
            
            # Calculate gross hours
            gross = (end_dt - start_dt).total_seconds() / 3600.0
            
            # OT = hours beyond 9h per shift
            if gross > 9.0:
                ot_hours = gross - 9.0
                emp_ot_hours[emp_id] += ot_hours
        except:
            pass
    
    # Filter to only OT-eligible employees (schemes A, B)
    eligible_ot = {}
    for emp_id, ot_hours in emp_ot_hours.items():
        scheme = emp_scheme.get(emp_id, 'A')
        if scheme in ['A', 'B']:
            eligible_ot[emp_id] = ot_hours
    
    if len(eligible_ot) < 2:
        return 0  # Need at least 2 employees to compare fairness
    
    # Calculate average OT
    total_ot = sum(eligible_ot.values())
    avg_ot = total_ot / len(eligible_ot)
    
    if avg_ot == 0:
        return 0  # No OT assigned, nothing to balance
    
    violations = 0
    
    # Flag outliers
    for emp_id, ot_hours in eligible_ot.items():
        # High OT burden
        if ot_hours > avg_ot * 1.5:
            score_book.soft(
                "S10",
                f"{emp_id}: OT hours {ot_hours:.1f}h significantly above average {avg_ot:.1f}h (unfair burden)"
            )
            violations += 1
        
        # Low OT (missed opportunity) - only flag if average is substantial
        elif ot_hours < avg_ot * 0.5 and avg_ot > 5.0:
            score_book.soft(
                "S10",
                f"{emp_id}: OT hours {ot_hours:.1f}h significantly below average {avg_ot:.1f}h (missed opportunity)"
            )
            violations += 1
    
    return violations
