"""S15: Maximize demand coverage score (filled/required).

Soft constraint that tracks demand fulfillment and encourages maximizing
the ratio of filled slots to required headcount.
"""

def add_constraints(model, ctx):
    """Encourage maximizing demand coverage ratio."""
    
    employees = ctx.get('employees', [])
    slots = ctx.get('slots', [])
    demand_items = ctx.get('demandItems', [])
    x = ctx.get('x', {})
    
    if not slots or not x:
        print(f"[S15] Demand Coverage Score Constraint (SOFT)")
        print(f"     Skipping: slots or decision variables not available")
        return
    
    print(f"[S15] Demand Coverage Score Constraint (SOFT)")
    print(f"     Total employees: {len(employees)}")
    print(f"     Total slots: {len(slots)}")
    
    # Calculate demand coverage opportunities
    total_demand_headcount = 0
    demands_with_slots = 0
    for demand in demand_items:
        headcount = demand.get('headcount', 0)
        total_demand_headcount += headcount * 7  # Assume 7-day planning horizon
        demands_with_slots += 1
    
    print(f"     Demands tracked: {demands_with_slots}")
    print(f"     Total demand positions: {total_demand_headcount}")
    print(f"     Current assignments: {sum(1 for _ in x)}")
    print(f"     Note: S15 is a soft constraint - coverage maximized via objective\n")


def score_violations(ctx, assignments, score_book):
    """Score violations for insufficient demand coverage.
    
    Checks each demand to ensure it meets its target headcount. Flags demands
    where filled positions are significantly below required headcount.
    """
    from collections import defaultdict
    
    slots = ctx.get('slots', [])
    demands = ctx.get('demands', [])
    
    if not slots or not demands or not assignments:
        return 0
    
    violations = 0
    
    # Build slot_id to slot mapping for quick lookup
    slot_map = {slot.get('slot_id'): slot for slot in slots}
    
    # Group assignments by demand_id and date
    demand_coverage = defaultdict(lambda: defaultdict(int))  # {demand_id: {date: filled_count}}
    
    for assignment in assignments:
        slot_id = assignment.get('slotId')
        if not slot_id or slot_id not in slot_map:
            continue
            
        slot = slot_map[slot_id]
        demand_id = slot.get('demand_id')
        date_str = slot.get('date')
        
        if demand_id and date_str:
            demand_coverage[demand_id][date_str] += 1
    
    # Build demand requirements mapping
    demand_requirements = {}
    for demand in demands:
        demand_id = demand.get('demandId')
        headcount = demand.get('headcount', 0)
        if demand_id:
            demand_requirements[demand_id] = headcount
    
    # Check each demand's coverage
    for demand_id, date_coverage in demand_coverage.items():
        required_headcount = demand_requirements.get(demand_id, 0)
        
        if required_headcount == 0:
            continue
        
        # Check coverage for each date
        for date_str, filled_count in date_coverage.items():
            coverage_ratio = filled_count / required_headcount if required_headcount > 0 else 0
            
            # Flag if coverage is below 80% of required headcount
            if coverage_ratio < 0.8:
                coverage_pct = coverage_ratio * 100
                score_book.soft(
                    "S15",
                    f"Demand {demand_id} on {date_str}: {filled_count}/{required_headcount} filled ({coverage_pct:.0f}% coverage)"
                )
                violations += 1
            
            # Additional flag for very low coverage (<50%)
            elif coverage_ratio < 0.5:
                coverage_pct = coverage_ratio * 100
                score_book.soft(
                    "S15",
                    f"Demand {demand_id} on {date_str}: CRITICAL - only {filled_count}/{required_headcount} filled ({coverage_pct:.0f}%)"
                )
                violations += 1
    
    # Also check for demands with no assignments at all
    for demand_id, required_headcount in demand_requirements.items():
        if required_headcount > 0 and demand_id not in demand_coverage:
            score_book.soft(
                "S15",
                f"Demand {demand_id} has NO assignments (requires {required_headcount})"
            )
            violations += 1
    
    return violations
