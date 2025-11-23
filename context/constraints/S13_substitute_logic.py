"""S13: Auto-substitute for unavailability (SOFT constraint).

Soft constraint that flags violations when employees are assigned during their
unavailable periods. Encourages using substitute employees instead.

Unavailability can be due to: leave, training, medical, or other reasons.
"""

from datetime import datetime, timedelta
from collections import defaultdict


def add_constraints(model, ctx):
    """
    S13 is a SOFT constraint - no model.Add() calls.
    
    Scoring happens post-solution via score_violations().
    """
    print(f"[S13] Substitute Logic (SOFT) - registered for post-solution scoring\n")


def score_violations(ctx, assignments, score_book):
    """
    Calculate S13 unavailability violations.
    
    For each assignment, check if the employee is marked unavailable on that date.
    Violation occurs when an unavailable employee is assigned to work.
    
    Unavailability periods are defined in employee records.
    
    Args:
        ctx: Context dict with employees
        assignments: List of assignment dicts from solver
        score_book: ScoreBook instance for recording violations
    
    Returns:
        Number of violations detected
    """
    
    employees = ctx.get('employees', [])
    
    # Build employee unavailability map
    emp_unavailability = {}
    
    for emp in employees:
        emp_id = emp.get('employeeId')
        unavailability_list = emp.get('unavailability', [])
        
        if unavailability_list:
            unavailable_dates = set()
            
            for period in unavailability_list:
                start_str = period.get('startDate')
                end_str = period.get('endDate')
                reason = period.get('reason', 'unavailable')
                
                if start_str and end_str:
                    try:
                        start_date = datetime.fromisoformat(start_str).date()
                        end_date = datetime.fromisoformat(end_str).date()
                        
                        # Add all dates in range
                        current = start_date
                        while current <= end_date:
                            unavailable_dates.add((current, reason))
                            current = current + timedelta(days=1)
                    except:
                        pass
            
            if unavailable_dates:
                emp_unavailability[emp_id] = unavailable_dates
    
    violations = 0
    
    # Check each assignment
    for assignment in assignments:
        emp_id = assignment.get('employeeId')
        date_str = assignment.get('date')
        
        if emp_id not in emp_unavailability:
            continue
        
        try:
            date_obj = datetime.fromisoformat(date_str).date()
            
            # Check if employee is unavailable on this date
            for unavailable_date, reason in emp_unavailability[emp_id]:
                if date_obj == unavailable_date:
                    score_book.soft(
                        "S13",
                        f"{emp_id} on {date_str}: assigned during unavailability period (reason: {reason})"
                    )
                    violations += 1
                    break
        except:
            pass
    
    return violations
