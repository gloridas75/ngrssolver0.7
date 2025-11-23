"""S11: Ensure adequate coverage on public holidays (SOFT constraint).

Soft constraint that encourages maintaining sufficient staffing levels on
public holidays. Violations occur when holiday coverage is below expected levels.

Public holidays are identified from the calendar configuration.
"""

from datetime import datetime
from collections import defaultdict


def add_constraints(model, ctx):
    """
    S11 is a SOFT constraint - no model.Add() calls.
    
    Scoring happens post-solution via score_violations().
    """
    print(f"[S11] Public Holiday Coverage (SOFT) - registered for post-solution scoring\n")


def score_violations(ctx, assignments, score_book):
    """
    Calculate S11 public holiday coverage violations.
    
    For each public holiday in the planning period, check if adequate staffing
    is maintained. Violation occurs if holiday shifts are understaffed compared
    to regular days.
    
    Public holidays are identified from calendar or special flags in demand items.
    
    Args:
        ctx: Context dict with planningHorizon, calendar
        assignments: List of assignment dicts from solver
        score_book: ScoreBook instance for recording violations
    
    Returns:
        Number of violations detected
    """
    
    planning_horizon = ctx.get('planningHorizon', {})
    calendar = ctx.get('calendar', {})
    demand_items = ctx.get('demandItems', [])
    
    # Get public holiday dates from calendar
    public_holidays = set()
    holidays_list = calendar.get('publicHolidays', [])
    
    for holiday in holidays_list:
        date_str = holiday.get('date') if isinstance(holiday, dict) else holiday
        if date_str:
            try:
                holiday_date = datetime.fromisoformat(date_str).date()
                public_holidays.add(holiday_date)
            except:
                pass
    
    if not public_holidays:
        return 0  # No holidays defined, nothing to check
    
    # Group assignments by date
    assignments_by_date = defaultdict(list)
    for assignment in assignments:
        date_str = assignment.get('date')
        if date_str:
            try:
                date_obj = datetime.fromisoformat(date_str).date()
                assignments_by_date[date_obj].append(assignment)
            except:
                pass
    
    # Calculate average staffing on non-holiday days
    non_holiday_counts = []
    for date, day_assignments in assignments_by_date.items():
        if date not in public_holidays:
            non_holiday_counts.append(len(day_assignments))
    
    if not non_holiday_counts:
        return 0  # No baseline to compare
    
    avg_staffing = sum(non_holiday_counts) / len(non_holiday_counts)
    
    violations = 0
    
    # Check each public holiday
    for holiday_date in public_holidays:
        if holiday_date in assignments_by_date:
            holiday_staffing = len(assignments_by_date[holiday_date])
            
            # Flag if holiday staffing is significantly below average (< 80%)
            if holiday_staffing < avg_staffing * 0.8:
                score_book.soft(
                    "S11",
                    f"Public holiday {holiday_date}: staffing {holiday_staffing} is below expected {avg_staffing:.1f} (80% threshold)"
                )
                violations += 1
        else:
            # No assignments on public holiday (if shifts exist)
            score_book.soft(
                "S11",
                f"Public holiday {holiday_date}: no assignments found"
            )
            violations += 1
    
    return violations
