"""Working Hours Calculation Utilities.

Canonical working-hours model:
  - gross_hours: Total duration (start → end)
  - lunch_hours: 1.0 if gross > 6.0, else 0.0
  - normal_hours: min(gross, 9.0) - lunch (working hours cap per shift is 9h)
  - ot_hours: max(0, gross - 9.0) (everything beyond 9h is OT)

Usage:
  - Weekly 44h cap: Sum of normal_hours only (exclude lunch & OT)
  - Monthly 72h OT cap: Sum of ot_hours only
  - Daily cap (14h, 13h, 9h by scheme): Can use gross_hours

Examples:
  09:00-18:00 → gross=9,  lunch=1, normal=8,  ot=0  (9h shift = 8h normal + 1h lunch)
  09:00-20:00 → gross=11, lunch=1, normal=8,  ot=2  (11h shift = 8h normal + 1h lunch + 2h OT)
  22:00-06:00 → gross=8,  lunch=1, normal=7,  ot=0  (8h overnight = 7h normal + 1h lunch)
  10:00-14:00 → gross=4,  lunch=0, normal=4,  ot=0  (4h short shift, no lunch)
"""

from datetime import datetime, time
from typing import Optional, Dict, List, Tuple


def span_hours(start_dt: datetime, end_dt: datetime) -> float:
    """Calculate gross hours between two datetimes.
    
    Handles overnight shifts correctly by considering the time span.
    
    Args:
        start_dt: Shift start time (datetime)
        end_dt: Shift end time (datetime)
    
    Returns:
        Gross hours as float (can be fractional)
    
    Examples:
        09:00-18:00 → 9.0 hours
        19:00-07:00 (next day) → 12.0 hours
        10:00-14:30 → 4.5 hours
    """
    delta = end_dt - start_dt
    total_seconds = delta.total_seconds()
    
    if total_seconds < 0:
        # Handle case where end is before start (overnight assumed, but should be handled by slot_builder)
        raise ValueError(f"End time {end_dt} is before start time {start_dt}")
    
    gross = total_seconds / 3600.0  # Convert seconds to hours
    return round(gross, 2)  # Round to 2 decimal places


def lunch_hours(gross: float) -> float:
    """Calculate lunch break duration.
    
    Industry standard: 1-hour meal break applies only if gross hours > 6.
    
    Args:
        gross: Gross hours worked
    
    Returns:
        Lunch hours: 1.0 if gross > 6.0, else 0.0
    
    Examples:
        gross=4.0  → 0.0 (no lunch on short shifts)
        gross=6.0  → 0.0 (exactly 6 hours, no lunch)
        gross=6.5  → 1.0 (more than 6, lunch applies)
        gross=9.0  → 1.0 (standard 9h shift with lunch)
        gross=11.0 → 1.0 (11h shift with lunch and OT)
    """
    return 1.0 if gross > 6.0 else 0.0


def split_normal_ot(gross: float) -> tuple:
    """Split working hours into normal and overtime.
    
    - Normal hours: capped at 9h per shift, minus lunch
    - OT hours: everything beyond 9h
    
    Args:
        gross: Gross hours worked
    
    Returns:
        Tuple of (normal_hours, ot_hours)
    
    Examples:
        gross=4.0  → (4.0, 0.0)     [4h normal, no OT, no lunch]
        gross=8.0  → (7.0, 0.0)     [8h gross = 7h normal + 1h lunch]
        gross=9.0  → (8.0, 0.0)     [9h gross = 8h normal + 1h lunch]
        gross=11.0 → (8.0, 2.0)     [11h gross = 8h normal + 1h lunch + 2h OT]
        gross=12.0 → (8.0, 3.0)     [12h gross = 8h normal + 1h lunch + 3h OT]
    """
    ln = lunch_hours(gross)
    
    # Normal hours = min(gross, 9.0) - lunch
    # This ensures normal never exceeds 8h when lunch applies, and never exceeds 9h when it doesn't
    normal = max(0.0, min(gross, 9.0) - ln)
    
    # OT hours = anything beyond 9h
    ot = max(0.0, gross - 9.0)
    
    return round(normal, 2), round(ot, 2)


def split_shift_hours(start_dt: datetime, end_dt: datetime) -> dict:
    """Complete breakdown of shift hours into all components.
    
    This is the primary function to use for any shift hour calculation.
    
    Args:
        start_dt: Shift start time (datetime)
        end_dt: Shift end time (datetime)
    
    Returns:
        Dictionary with keys:
        - 'gross': Total duration in hours
        - 'lunch': Meal break hours (0.0 or 1.0)
        - 'normal': Normal working hours (for 44h weekly cap)
        - 'ot': Overtime hours (for 72h monthly cap)
        - 'paid': Total paid hours (gross - lunch + any adjustments, typically = gross)
    
    Examples:
        09:00-18:00 →
        {
            'gross': 9.0,
            'lunch': 1.0,
            'normal': 8.0,
            'ot': 0.0,
            'paid': 9.0
        }
        
        09:00-20:00 →
        {
            'gross': 11.0,
            'lunch': 1.0,
            'normal': 8.0,
            'ot': 2.0,
            'paid': 11.0
        }
        
        19:00-23:30 →
        {
            'gross': 4.5,
            'lunch': 0.0,
            'normal': 4.5,
            'ot': 0.0,
            'paid': 4.5
        }
    """
    gross = span_hours(start_dt, end_dt)
    ln = lunch_hours(gross)
    normal, ot = split_normal_ot(gross)
    
    return {
        'gross': gross,
        'lunch': ln,
        'normal': normal,
        'ot': ot,
        'paid': gross  # In most systems, employee gets paid for full hours (including lunch time)
    }


def validate_shift_hours(start_dt: datetime, end_dt: datetime, max_gross_by_scheme: Optional[Dict] = None) -> dict:
    """Validate shift against scheme limits and return detailed breakdown.
    
    Args:
        start_dt: Shift start time
        end_dt: Shift end time
        max_gross_by_scheme: Optional dict mapping scheme -> max gross hours
                            Defaults to: {'A': 14, 'B': 13, 'P': 9}
    
    Returns:
        Dictionary with:
        - 'valid': True if shift is valid
        - 'hours': Complete hour breakdown (from split_shift_hours)
        - 'scheme_violations': List of scheme violations if any
    
    Examples:
        # Standard 8h shift for Scheme A
        result = validate_shift_hours(dt1, dt2, {'A': 14})
        # {'valid': True, 'hours': {...}, 'scheme_violations': []}
        
        # 15h shift exceeds Scheme A limit
        result = validate_shift_hours(dt1, dt2, {'A': 14})
        # {'valid': False, 'hours': {...}, 'scheme_violations': ['Scheme A max 14h']}
    """
    if max_gross_by_scheme is None:
        max_gross_by_scheme = {'A': 14, 'B': 13, 'P': 9}
    
    hours = split_shift_hours(start_dt, end_dt)
    violations = []
    
    # Check against each scheme's max gross hours
    for scheme, max_hours in max_gross_by_scheme.items():
        if hours['gross'] > max_hours:
            violations.append(f"Scheme {scheme}: gross hours {hours['gross']}h exceeds max {max_hours}h")
    
    return {
        'valid': len(violations) == 0,
        'hours': hours,
        'scheme_violations': violations
    }


# ============ SUMMARY HELPERS ============

def calculate_weekly_normal_hours(shifts: list) -> float:
    """Calculate total normal (working) hours for a week from list of shifts.
    
    Use this for 44h weekly cap checks.
    
    Args:
        shifts: List of (start_dt, end_dt) tuples
    
    Returns:
        Sum of normal_hours (excludes lunch and OT)
    """
    total = 0.0
    for start_dt, end_dt in shifts:
        hours_dict = split_shift_hours(start_dt, end_dt)
        total += hours_dict['normal']
    return round(total, 2)


def calculate_monthly_ot_hours(shifts: list) -> float:
    """Calculate total OT hours for a month from list of shifts.
    
    Use this for 72h monthly OT cap checks.
    
    Args:
        shifts: List of (start_dt, end_dt) tuples
    
    Returns:
        Sum of ot_hours only
    """
    total = 0.0
    for start_dt, end_dt in shifts:
        hours_dict = split_shift_hours(start_dt, end_dt)
        total += hours_dict['ot']
    return round(total, 2)


def calculate_daily_gross_hours(shifts_same_day: list) -> float:
    """Calculate total gross hours for a single day.
    
    Use this for daily cap checks (14h/13h/9h by scheme).
    
    Args:
        shifts_same_day: List of (start_dt, end_dt) tuples for same calendar day
    
    Returns:
        Sum of gross_hours for the day
    """
    total = 0.0
    for start_dt, end_dt in shifts_same_day:
        total += span_hours(start_dt, end_dt)
    return round(total, 2)
