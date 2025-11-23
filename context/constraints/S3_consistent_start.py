"""S3: Prefer consistent daily start times per employee (SOFT constraint).

Soft constraint encouraging employees to work the same shift times consistently
(e.g., always 08:00 start, avoiding switching between morning/evening/night shifts).

Violations occur when an employee works different shift start times.
"""

from collections import defaultdict
from datetime import datetime


def add_constraints(model, ctx):
    """
    S3 is a SOFT constraint - no model.Add() calls.
    
    Scoring happens post-solution via score_violations().
    """
    print(f"[S3] Consistent Shift Start Times (SOFT) - registered for post-solution scoring\n")


def score_violations(ctx, assignments, score_book):
    """
    Calculate S3 shift start time consistency violations.
    
    For each employee, track all unique shift start times they're assigned.
    Violation occurs for each additional start time beyond the first (most common) one.
    
    Example:
    - Employee works 5 days at 08:00 start, 2 days at 14:00 start
    - Most common: 08:00 (5 occurrences)
    - Violations: 2 (the 2 days at 14:00)
    
    Args:
        ctx: Context dict
        assignments: List of assignment dicts from solver
        score_book: ScoreBook instance for recording violations
    
    Returns:
        Number of violations detected
    """
    
    # Group assignments by employee and track start times
    emp_start_times = defaultdict(list)  # emp_id -> [(date, start_time)]
    
    for assignment in assignments:
        emp_id = assignment.get('employeeId')
        date_str = assignment.get('date')
        start_dt_str = assignment.get('startDateTime')
        
        if not emp_id or not start_dt_str:
            continue
        
        try:
            start_dt = datetime.fromisoformat(start_dt_str)
            start_time = start_dt.time()
            emp_start_times[emp_id].append((date_str, start_time))
        except:
            pass
    
    violations = 0
    
    # For each employee, check consistency
    for emp_id, start_times_list in emp_start_times.items():
        if len(start_times_list) <= 1:
            continue  # Single assignment, no consistency issue
        
        # Count frequency of each start time
        time_counts = defaultdict(int)
        for date_str, start_time in start_times_list:
            time_counts[start_time] += 1
        
        # Find most common start time
        most_common_time = max(time_counts, key=time_counts.get)
        most_common_count = time_counts[most_common_time]
        
        # All other start times are violations
        for date_str, start_time in start_times_list:
            if start_time != most_common_time:
                score_book.soft(
                    "S3",
                    f"{emp_id} on {date_str}: start time {start_time.strftime('%H:%M')} differs from usual {most_common_time.strftime('%H:%M')}"
                )
                violations += 1
    
    return violations
