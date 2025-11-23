"""S7: Zone preferences optimization (SOFT constraint).

Soft constraint that encourages assigning employees to shifts in their preferred zones/locations.
Violations occur when employees are assigned outside their preferred zones.
"""

from collections import defaultdict


def add_constraints(model, ctx):
    """
    S7 is a SOFT constraint - no model.Add() calls.
    
    Scoring happens post-solution via score_violations().
    """
    print(f"[S7] Zone Preferences (SOFT) - registered for post-solution scoring\n")


def score_violations(ctx, assignments, score_book):
    """
    Calculate S7 zone preference violations.
    
    For each assignment, check if the employee is assigned to a zone/location
    they prefer. Violations occur when assigned to non-preferred zones.
    
    Zone can be defined via:
    - Employee preferences.preferredZones
    - Employee preferences.preferredSites (site-level preference)
    - Employee preferences.preferredOUs (organizational unit preference)
    
    Args:
        ctx: Context dict with employees, demand_items
        assignments: List of assignment dicts from solver
        score_book: ScoreBook instance for recording violations
    
    Returns:
        Number of violations detected
    """
    
    employees = ctx.get('employees', [])
    demand_items = ctx.get('demandItems', [])
    
    # Build employee zone preferences
    emp_zone_prefs = {}
    for emp in employees:
        emp_id = emp.get('employeeId')
        prefs = emp.get('preferences', {})
        
        if prefs:
            emp_zone_prefs[emp_id] = {
                'preferredZones': prefs.get('preferredZones', []),
                'preferredSites': prefs.get('preferredSites', []),
                'preferredOUs': prefs.get('preferredOUs', []),
                'unpreferredZones': prefs.get('unpreferredZones', []),
                'unpreferredSites': prefs.get('unpreferredSites', [])
            }
    
    # Build demand metadata (site, OU, zone)
    demand_metadata = {}
    for demand in demand_items:
        demand_id = demand.get('demandId')
        demand_metadata[demand_id] = {
            'siteId': demand.get('siteId'),
            'ouId': demand.get('ouId'),
            'zone': demand.get('zone')  # If zone field exists
        }
    
    violations = 0
    
    for assignment in assignments:
        emp_id = assignment.get('employeeId')
        demand_id = assignment.get('demandId')
        date_str = assignment.get('date')
        
        if emp_id not in emp_zone_prefs:
            continue
        
        prefs = emp_zone_prefs[emp_id]
        metadata = demand_metadata.get(demand_id, {})
        
        site_id = metadata.get('siteId')
        ou_id = metadata.get('ouId')
        zone = metadata.get('zone')
        
        # Check unpreferred zones
        if zone and zone in prefs.get('unpreferredZones', []):
            score_book.soft(
                "S7",
                f"{emp_id} on {date_str}: assigned to unpreferred zone {zone}"
            )
            violations += 1
        
        # Check unpreferred sites
        if site_id and site_id in prefs.get('unpreferredSites', []):
            score_book.soft(
                "S7",
                f"{emp_id} on {date_str}: assigned to unpreferred site {site_id}"
            )
            violations += 1
        
        # Check preferred zones (if specified and not matched)
        preferred_zones = prefs.get('preferredZones', [])
        if preferred_zones and zone and zone not in preferred_zones:
            score_book.soft(
                "S7",
                f"{emp_id} on {date_str}: assigned to zone {zone} but prefers {','.join(preferred_zones)}"
            )
            violations += 1
        
        # Check preferred sites (if specified and not matched)
        preferred_sites = prefs.get('preferredSites', [])
        if preferred_sites and site_id and site_id not in preferred_sites:
            score_book.soft(
                "S7",
                f"{emp_id} on {date_str}: assigned to site {site_id} but prefers {','.join(preferred_sites)}"
            )
            violations += 1
        
        # Check preferred OUs (if specified and not matched)
        preferred_ous = prefs.get('preferredOUs', [])
        if preferred_ous and ou_id and ou_id not in preferred_ous:
            score_book.soft(
                "S7",
                f"{emp_id} on {date_str}: assigned to OU {ou_id} but prefers {','.join(preferred_ous)}"
            )
            violations += 1
    
    return violations
