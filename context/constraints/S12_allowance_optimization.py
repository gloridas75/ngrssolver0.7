"""S12: Optimize allowance scheduling (SOFT constraint).

Soft constraint that encourages optimal distribution of allowance-eligible shifts
(night, weekend, holiday shifts) to minimize costs while maintaining coverage.

Violations occur when allowances are distributed inefficiently.
"""

from datetime import datetime
from collections import defaultdict


def add_constraints(model, ctx):
    """
    S12 is a SOFT constraint - no model.Add() calls.
    
    Scoring happens post-solution via score_violations().
    """
    print(f"[S12] Allowance Optimization (SOFT) - registered for post-solution scoring\n")


def score_violations(ctx, assignments, score_book):
    """
    Calculate S12 allowance optimization violations.
    
    Track allowance-eligible shifts (night, weekend, holiday) and check for
    efficient distribution. Violations occur when:
    - Same employees consistently get high-allowance shifts (unfair concentration)
    - Allowance shifts are spread too thin (inefficient)
    
    Strategy: Flag outliers in allowance hours per employee.
    
    Args:
        ctx: Context dict with employees, calendar
        assignments: List of assignment dicts from solver
        score_book: ScoreBook instance for recording violations
    
    Returns:
        Number of violations detected
    """
    
    calendar = ctx.get('calendar', {})
    
    # Get public holidays
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
    
    # Track allowance hours per employee
    emp_allowance_hours = defaultdict(float)
    
    for assignment in assignments:
        emp_id = assignment.get('employeeId')
        shift_code = assignment.get('shiftCode', '')
        date_str = assignment.get('date')
        
        try:
            start_dt = datetime.fromisoformat(assignment.get('startDateTime'))
            end_dt = datetime.fromisoformat(assignment.get('endDateTime'))
            date_obj = datetime.fromisoformat(date_str).date()
            
            shift_hours = (end_dt - start_dt).total_seconds() / 3600.0
            
            # Check if shift qualifies for allowance
            is_allowance_shift = False
            
            # Night shift allowance
            if shift_code in ['N', 'NIGHT']:
                is_allowance_shift = True
            
            # Weekend allowance (Saturday/Sunday)
            elif date_obj.weekday() >= 5:  # 5=Saturday, 6=Sunday
                is_allowance_shift = True
            
            # Public holiday allowance
            elif date_obj in public_holidays:
                is_allowance_shift = True
            
            if is_allowance_shift:
                emp_allowance_hours[emp_id] += shift_hours
        except:
            pass
    
    if len(emp_allowance_hours) < 2:
        return 0  # Not enough data to check distribution
    
    # Calculate average allowance hours
    total_allowance = sum(emp_allowance_hours.values())
    avg_allowance = total_allowance / len(emp_allowance_hours)
    
    if avg_allowance == 0:
        return 0  # No allowance shifts assigned
    
    violations = 0
    
    # Flag outliers (high concentration)
    for emp_id, allowance_hours in emp_allowance_hours.items():
        # High allowance concentration (>2x average)
        if allowance_hours > avg_allowance * 2.0:
            score_book.soft(
                "S12",
                f"{emp_id}: allowance hours {allowance_hours:.1f}h significantly above average {avg_allowance:.1f}h (cost concentration)"
            )
            violations += 1
    
    return violations
