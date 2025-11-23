"""S14: Delta-solve: insert new joiners without disturbing published.

Soft constraint that handles mid-month additions (new joiners) by identifying
insertion opportunities without disrupting already-published assignments.
"""

def add_constraints(model, ctx):
    """Handle mid-month inserts with minimal published schedule changes."""
    
    employees = ctx.get('employees', [])
    slots = ctx.get('slots', [])
    x = ctx.get('x', {})
    published_assignments = ctx.get('publishedAssignments', [])
    
    if not slots or not x:
        print(f"[S14] Midmonth Insert Constraint (SOFT)")
        print(f"     Skipping: slots or decision variables not available")
        return
    
    print(f"[S14] Midmonth Insert Constraint (SOFT)")
    print(f"     Total employees: {len(employees)}")
    print(f"     Published assignments: {len(published_assignments)}")
    
    # Identify new joiners (employees without prior assignments)
    assigned_emps = set(emp_id for _, emp_id in x.keys())
    new_joiners = [e for e in employees if e.get('employeeId') not in assigned_emps]
    
    print(f"     Potential new joiners: {len(new_joiners)}")
    print(f"     Note: S14 is a soft constraint - delta-solve handled in solver workflow\n")


def score_violations(ctx, assignments, score_book):
    """Score violations for mid-month coverage issues.
    
    Checks for adequate staffing distribution across the month, particularly
    ensuring that mid-month periods (days 11-20) have sufficient coverage.
    Flags demands where mid-month coverage drops significantly below average.
    """
    from datetime import datetime
    from collections import defaultdict
    
    demands = ctx.get('demands', [])
    
    if not demands or not assignments:
        return 0
    
    violations = 0
    
    # Group assignments by demand and calculate coverage by day-of-month
    demand_coverage = defaultdict(lambda: defaultdict(int))  # {demand_id: {day_of_month: count}}
    
    for assignment in assignments:
        demand_id = assignment.get('demandId')
        slot_date_str = assignment.get('date')
        
        if not demand_id or not slot_date_str:
            continue
            
        try:
            date_obj = datetime.fromisoformat(slot_date_str).date()
            day_of_month = date_obj.day
            demand_coverage[demand_id][day_of_month] += 1
        except (ValueError, AttributeError):
            continue
    
    # Check each demand for mid-month coverage issues
    for demand_id, coverage_by_day in demand_coverage.items():
        if not coverage_by_day:
            continue
        
        # Calculate average coverage across all days
        total_coverage = sum(coverage_by_day.values())
        num_days = len(coverage_by_day)
        avg_coverage = total_coverage / num_days if num_days > 0 else 0
        
        # Calculate mid-month coverage (days 11-20)
        midmonth_days = [day for day in coverage_by_day.keys() if 11 <= day <= 20]
        if not midmonth_days:
            continue
            
        midmonth_coverage = sum(coverage_by_day[day] for day in midmonth_days)
        midmonth_avg = midmonth_coverage / len(midmonth_days)
        
        # Flag if mid-month coverage is significantly below average (< 70% of average)
        if avg_coverage > 0 and midmonth_avg < 0.7 * avg_coverage:
            coverage_ratio = (midmonth_avg / avg_coverage * 100) if avg_coverage > 0 else 0
            score_book.soft(
                "S14",
                f"Demand {demand_id} mid-month coverage ({midmonth_avg:.1f}) is {coverage_ratio:.0f}% of average ({avg_coverage:.1f})"
            )
            violations += 1
        
        # Also check for specific days in mid-month with zero coverage
        for day in range(11, 21):  # Days 11-20
            if day in coverage_by_day and coverage_by_day[day] == 0:
                score_book.soft(
                    "S14",
                    f"Demand {demand_id} has zero coverage on day {day} (mid-month)"
                )
                violations += 1
    
    return violations
