"""S2: Respect employee shift preferences (SOFT constraint).

Soft constraint that encourages respecting employee shift preferences:
- Preferred shifts (e.g., day over night)
- Preferred teams/locations
- Preferred work patterns

Violations reduce soft score but don't block solutions.
"""

from datetime import datetime


def add_constraints(model, ctx):
    """
    S2 is a SOFT constraint - no model.Add() calls.
    
    Scoring happens post-solution via score_violations().
    """
    print(f"[S2] Employee Preferences (SOFT) - registered for post-solution scoring\n")


def score_violations(ctx, assignments, score_book):
    """
    Calculate S2 employee preference violations.
    
    Check each assignment against employee preferences:
    - preferredShifts: Employee prefers certain shift types
    - unpreferredShifts: Employee wants to avoid certain shifts
    - preferredTeams: Employee prefers certain teams
    - preferredSites: Employee prefers certain locations
    
    Args:
        ctx: Context dict with employees
        assignments: List of assignment dicts from solver
        score_book: ScoreBook instance for recording violations
    
    Returns:
        Number of violations detected
    """
    
    employees = ctx.get('employees', [])
    demand_items = ctx.get('demandItems', [])
    
    # Build employee preferences map
    emp_prefs = {}
    for emp in employees:
        emp_id = emp.get('employeeId')
        prefs = emp.get('preferences', {})
        if prefs:
            emp_prefs[emp_id] = prefs
    
    # Build demand metadata (team, site)
    demand_metadata = {}
    for demand in demand_items:
        demand_id = demand.get('demandId')
        demand_metadata[demand_id] = {
            'teamId': demand.get('teamId'),
            'siteId': demand.get('siteId'),
            'ouId': demand.get('ouId')
        }
    
    violations = 0
    
    for assignment in assignments:
        emp_id = assignment.get('employeeId')
        shift_code = assignment.get('shiftCode')
        demand_id = assignment.get('demandId')
        date_str = assignment.get('date')
        
        if emp_id not in emp_prefs:
            continue
        
        prefs = emp_prefs[emp_id]
        demand_meta = demand_metadata.get(demand_id, {})
        
        # Check unpreferred shifts
        unpreferred_shifts = prefs.get('unpreferredShifts', [])
        if shift_code in unpreferred_shifts:
            score_book.soft(
                "S2",
                f"{emp_id} on {date_str}: assigned unpreferred shift {shift_code}"
            )
            violations += 1
        
        # Check preferred shifts (if specified and not matched)
        preferred_shifts = prefs.get('preferredShifts', [])
        if preferred_shifts and shift_code not in preferred_shifts:
            # Only flag if employee has explicit preferences
            score_book.soft(
                "S2",
                f"{emp_id} on {date_str}: assigned {shift_code} but prefers {','.join(preferred_shifts)}"
            )
            violations += 1
        
        # Check unpreferred teams
        unpreferred_teams = prefs.get('unpreferredTeams', [])
        team_id = demand_meta.get('teamId')
        if team_id and team_id in unpreferred_teams:
            score_book.soft(
                "S2",
                f"{emp_id} on {date_str}: assigned to unpreferred team {team_id}"
            )
            violations += 1
        
        # Check preferred teams (if specified and not matched)
        preferred_teams = prefs.get('preferredTeams', [])
        if preferred_teams and team_id and team_id not in preferred_teams:
            score_book.soft(
                "S2",
                f"{emp_id} on {date_str}: assigned to {team_id} but prefers {','.join(preferred_teams)}"
            )
            violations += 1
        
        # Check unpreferred sites
        unpreferred_sites = prefs.get('unpreferredSites', [])
        site_id = demand_meta.get('siteId')
        if site_id and site_id in unpreferred_sites:
            score_book.soft(
                "S2",
                f"{emp_id} on {date_str}: assigned to unpreferred site {site_id}"
            )
            violations += 1
        
        # Check preferred sites (if specified and not matched)
        preferred_sites = prefs.get('preferredSites', [])
        if preferred_sites and site_id and site_id not in preferred_sites:
            score_book.soft(
                "S2",
                f"{emp_id} on {date_str}: assigned to {site_id} but prefers {','.join(preferred_sites)}"
            )
            violations += 1
    
    return violations
