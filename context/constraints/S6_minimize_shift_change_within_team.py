"""S6: Minimize shift changes within team (SOFT constraint).

Soft constraint that discourages employees from working in multiple teams
during the planning period. Encourages team stability and cohesion.

Violations occur when an employee is assigned to multiple different teams.
"""

from collections import defaultdict


def add_constraints(model, ctx):
    """
    S6 is a SOFT constraint - no model.Add() calls.
    
    Scoring happens post-solution via score_violations().
    """
    print(f"[S6] Minimize Team Changes (SOFT) - registered for post-solution scoring\n")


def score_violations(ctx, assignments, score_book):
    """
    Calculate S6 team change violations.
    
    For each employee, track how many different teams they're assigned to.
    Violation occurs for each additional team beyond the first.
    
    Example:
    - Employee works 5 days in Team A, 2 days in Team B
    - Violations: 2 (the 2 days in the second team)
    
    Args:
        ctx: Context dict with demand_items
        assignments: List of assignment dicts from solver
        score_book: ScoreBook instance for recording violations
    
    Returns:
        Number of violations detected
    """
    
    demand_items = ctx.get('demandItems', [])
    
    # Build demand -> team mapping
    demand_teams = {}
    for demand in demand_items:
        demand_id = demand.get('demandId')
        team_id = demand.get('teamId')
        if demand_id and team_id:
            demand_teams[demand_id] = team_id
    
    # Track teams per employee
    emp_teams = defaultdict(list)  # emp_id -> [(date, team_id)]
    
    for assignment in assignments:
        emp_id = assignment.get('employeeId')
        demand_id = assignment.get('demandId')
        date_str = assignment.get('date')
        
        team_id = demand_teams.get(demand_id)
        
        if emp_id and team_id and date_str:
            emp_teams[emp_id].append((date_str, team_id))
    
    violations = 0
    
    # Check each employee for multiple team assignments
    for emp_id, team_list in emp_teams.items():
        if len(team_list) <= 1:
            continue
        
        # Count team frequencies
        team_counts = defaultdict(int)
        for date_str, team_id in team_list:
            team_counts[team_id] += 1
        
        # If employee works in multiple teams
        if len(team_counts) > 1:
            # Primary team is the most common one
            # Cast to list to satisfy type checker
            primary_team = max(list(team_counts.keys()), key=lambda t: team_counts[t])
            
            # All assignments to other teams are violations
            for date_str, team_id in team_list:
                if team_id != primary_team:
                    score_book.soft(
                        "S6",
                        f"{emp_id} on {date_str}: assigned to team {team_id} but primary team is {primary_team}"
                    )
                    violations += 1
    
    return violations
