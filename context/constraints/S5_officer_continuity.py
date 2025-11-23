"""S5: Prefer continuity of same officer at site across days (SOFT constraint).

Soft constraint that encourages keeping the same employee assigned to a demand/site
across consecutive days. This improves team cohesion and knowledge continuity.

Violations occur when different employees are assigned to the same demand on consecutive days.
"""

from collections import defaultdict
from datetime import datetime, timedelta


def add_constraints(model, ctx):
    """
    S5 is a SOFT constraint - no model.Add() calls.
    
    Scoring happens post-solution via score_violations().
    """
    print(f"[S5] Officer Continuity (SOFT) - registered for post-solution scoring\n")


def score_violations(ctx, assignments, score_book):
    """
    Calculate S5 officer continuity violations.
    
    For each demand, check if the same employees are assigned on consecutive days.
    Violation occurs when different employees work the same demand on consecutive days.
    
    Strategy:
    - Group assignments by (demandId, date)
    - For each demand, check consecutive date pairs
    - If employee sets differ between consecutive days, count as violation
    
    Args:
        ctx: Context dict
        assignments: List of assignment dicts from solver
        score_book: ScoreBook instance for recording violations
    
    Returns:
        Number of violations detected
    """
    
    # Group assignments by demand and date
    demand_date_employees = defaultdict(lambda: defaultdict(set))  # demand_id -> date -> {emp_ids}
    
    for assignment in assignments:
        demand_id = assignment.get('demandId')
        date_str = assignment.get('date')
        emp_id = assignment.get('employeeId')
        
        if demand_id and date_str and emp_id:
            try:
                date_obj = datetime.fromisoformat(date_str).date()
                demand_date_employees[demand_id][date_obj].add(emp_id)
            except:
                pass
    
    violations = 0
    
    # Check continuity for each demand
    for demand_id, date_employees in demand_date_employees.items():
        sorted_dates = sorted(date_employees.keys())
        
        if len(sorted_dates) < 2:
            continue
        
        # Check consecutive date pairs
        for i in range(len(sorted_dates) - 1):
            date1 = sorted_dates[i]
            date2 = sorted_dates[i + 1]
            
            # Check if dates are consecutive
            if (date2 - date1).days != 1:
                continue
            
            emp_set1 = date_employees[date1]
            emp_set2 = date_employees[date2]
            
            # Check if employee sets are different
            # Ideal: same employees on both days
            # Violation: different employees (any change)
            
            # Count employees who are NOT continuous (present one day but not the next)
            employees_left = emp_set1 - emp_set2  # In day1 but not day2
            employees_joined = emp_set2 - emp_set1  # In day2 but not day1
            
            # Record violations for discontinuity
            for emp_id in employees_left:
                score_book.soft(
                    "S5",
                    f"Demand {demand_id}: {emp_id} worked {date1} but not consecutive day {date2} (continuity break)"
                )
                violations += 1
            
            for emp_id in employees_joined:
                score_book.soft(
                    "S5",
                    f"Demand {demand_id}: {emp_id} started {date2} but did not work previous day {date1} (continuity break)"
                )
                violations += 1
    
    return violations
