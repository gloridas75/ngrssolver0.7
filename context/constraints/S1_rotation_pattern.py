"""S1: Rotation pattern compliance (SOFT constraint).

Soft constraint that encourages assignments to follow the rotation patterns
defined in shift configurations. Rotation patterns like [D,D,D,O,O,D,D] define
a repeating cycle for scheduling.

Violations are scored but don't block solutions.
"""

from collections import defaultdict
from datetime import datetime


def add_constraints(model, ctx):
    """
    S1 is a SOFT constraint - no model.Add() calls.
    
    This function just logs that S1 is registered. Actual violation scoring
    happens post-solution in calculate_scores() or via score_violations().
    
    Args:
        model: CP-SAT model (not modified for soft constraints)
        ctx: Context dict with planning data
    """
    
    print(f"[S1] Rotation Pattern Compliance (SOFT) - registered for post-solution scoring\n")


def score_violations(ctx, assignments, score_book):
    """
    Calculate S1 rotation pattern compliance violations.
    
    For each assignment, check if the shift matches the expected rotation pattern
    for that demand on that date. Violations occur when assigned shift doesn't
    match the rotation sequence.
    
    Args:
        ctx: Context dict with demand_items, planningHorizon
        assignments: List of assignment dicts from solver
        score_book: ScoreBook instance for recording violations
    
    Returns:
        Number of violations detected
    """
    
    demand_items = ctx.get('demandItems', [])
    planning_horizon = ctx.get('planningHorizon', {})
    
    # Build rotation patterns map
    rotation_patterns = {}
    for demand in demand_items:
        demand_id = demand.get('demandId')
        shift_start_date_str = demand.get('shiftStartDate', planning_horizon.get('startDate'))
        
        for shift_group in demand.get('shifts', []):
            rotation_seq = shift_group.get('rotationSequence', [])
            
            if rotation_seq and demand_id:
                try:
                    anchor_date = datetime.fromisoformat(shift_start_date_str).date()
                    rotation_patterns[demand_id] = {
                        'sequence': rotation_seq,
                        'anchor_date': anchor_date,
                        'cycle_days': len(rotation_seq)
                    }
                except:
                    pass
    
    violations = 0
    
    for assignment in assignments:
        demand_id = assignment.get('demandId')
        date_str = assignment.get('date')
        shift_code = assignment.get('shiftCode')
        emp_id = assignment.get('employeeId')
        
        if demand_id not in rotation_patterns:
            continue
        
        try:
            pattern = rotation_patterns[demand_id]
            rotation_seq = pattern['sequence']
            anchor_date = pattern['anchor_date']
            cycle_days = pattern['cycle_days']
            
            # Calculate which day in rotation cycle this date represents
            assignment_date = datetime.fromisoformat(date_str).date()
            days_from_anchor = (assignment_date - anchor_date).days
            rotation_index = days_from_anchor % cycle_days
            
            expected_shift = rotation_seq[rotation_index]
            
            # Skip if shift_code is empty or None
            if not shift_code:
                continue
            
            # Check if assigned shift matches expected (any mismatch counts)
            if shift_code != expected_shift:
                score_book.soft(
                    "S1",
                    f"{emp_id} on {date_str}: assigned {shift_code} but rotation expects {expected_shift} (demand {demand_id})"
                )
                violations += 1
                
        except Exception as e:
            # Skip invalid data
            pass
    
    return violations
