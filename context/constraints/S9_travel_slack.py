"""S9: Add buffer minutes for travel & staging (SOFT constraint).

Soft constraint that encourages additional buffer time between shifts at different
locations, beyond the minimum rest requirement. Improves employee comfort and
reduces travel stress.

This is a soft version of C14 (travel time), encouraging generous buffers.
"""

from datetime import datetime, timedelta
from collections import defaultdict


def add_constraints(model, ctx):
    """
    S9 is a SOFT constraint - no model.Add() calls.
    
    Scoring happens post-solution via score_violations().
    """
    print(f"[S9] Travel Slack Buffer (SOFT) - registered for post-solution scoring\n")


def score_violations(ctx, assignments, score_book):
    """
    Calculate S9 travel slack buffer violations.
    
    For consecutive shifts at different sites, check if there's adequate buffer time
    for travel. Recommended buffer: 30 minutes + travel time (total ~45-60 minutes).
    
    Violations occur when buffer between different-site shifts is less than ideal.
    
    Args:
        ctx: Context dict with demand_items
        assignments: List of assignment dicts from solver
        score_book: ScoreBook instance for recording violations
    
    Returns:
        Number of violations detected
    """
    
    demand_items = ctx.get('demandItems', [])
    
    # Get travel time configuration
    constraint_list = ctx.get('constraintList', [])
    min_travel_minutes = 30  # Default
    
    for constraint in constraint_list:
        if constraint.get('id') == 'travelTimeBetweenSites':
            min_travel_minutes = constraint.get('params', {}).get('minTravelMinutes', 30)
            break
    
    # Recommended buffer: travel time + staging/prep time (e.g., 30 + 30 = 60 min)
    recommended_buffer_minutes = min_travel_minutes + 30
    recommended_buffer = timedelta(minutes=recommended_buffer_minutes)
    
    # Build demand -> site mapping
    demand_sites = {}
    for demand in demand_items:
        demand_id = demand.get('demandId')
        site_id = demand.get('siteId')
        if demand_id and site_id:
            demand_sites[demand_id] = site_id
    
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
        
        # Check consecutive pairs for travel
        for i in range(len(sorted_assignments) - 1):
            a1 = sorted_assignments[i]
            a2 = sorted_assignments[i + 1]
            
            demand1 = a1.get('demandId')
            demand2 = a2.get('demandId')
            
            site1 = demand_sites.get(demand1)
            site2 = demand_sites.get(demand2)
            
            # Only check if sites are different
            if not site1 or not site2 or site1 == site2:
                continue
            
            try:
                end1 = datetime.fromisoformat(a1.get('endDateTime'))
                start2 = datetime.fromisoformat(a2.get('startDateTime'))
                
                buffer_time = start2 - end1
                
                # If buffer is less than recommended, flag as soft violation
                if buffer_time < recommended_buffer:
                    buffer_minutes = buffer_time.total_seconds() / 60.0
                    score_book.soft(
                        "S9",
                        f"{emp_id}: travel buffer {buffer_minutes:.0f}min between sites {site1} and {site2} is below recommended {recommended_buffer_minutes}min"
                    )
                    violations += 1
            except:
                pass
    
    return violations
