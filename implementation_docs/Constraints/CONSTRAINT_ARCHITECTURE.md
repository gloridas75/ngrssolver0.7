# Constraint Architecture & Implementation Guide

## Overview

The NGRS solver uses a two-phase constraint approach:
1. **Model-Level Constraints** (CP-SAT): Hard constraints that prevent infeasible solutions during solving
2. **Post-Solution Validation**: Hard/Soft constraint scoring that assigns violation counts to solutions

## Phase 1: Model-Level Constraints (in `context/constraints/`)

These are implemented in `add_constraints(model, ctx)` functions that directly modify the CP-SAT model by adding constraints via `model.Add()`.

### Implemented Constraints

| Constraint | Status | Implementation | Violations |
|------------|--------|---|---|
| **C1** | ✅ Post-only | Daily gross hours by scheme (A≤14h, B≤13h, P≤9h) | Validated in solver_engine |
| **C2** | ✅ Post-only | Weekly normal hours (≤44h) + Monthly OT (≤72h) | Validated in solver_engine |
| **C3** | ✅ Post-only | Max consecutive working days (≤12) | Validated in solver_engine |
| **C4** | ✅ Partial | Min rest between shifts (8h/11h default) | Model: Disjunctive constraints added |
| **C5** | ✅ Post-only | Min off-days per week (≥1 per 7 days) | Validated in solver_engine |
| **C6** | ✅ Post-only | Part-timer weekly limits | Validated in solver_engine |
| **C7** | ✅ Post-only | License/qualification validity | Validated in solver_engine |
| **C8** | ✅ Post-only | Provisional license (PDL) validity | Validated in solver_engine |
| **C9** | ✅ Post-only | Gender balance (soft via scoring) | Validated in solver_engine |
| **C10** | ✅ Enforced | Skill/role match via employee whitelisting | 0 violations when whitelisted |
| **C11** | ✅ Enforced | Rank/product type match via whitelisting | 0 violations when whitelisted |
| **C12** | ✅ Info | Team completeness (soft, info-only) | Informational |
| **C13** | ⏳ TODO | Regulatory fee capture (senior staff %) | Optional/nice-to-have |
| **C14** | ⏳ TODO | Travel time between locations | Optional/nice-to-have |
| **C15** | ✅ Post-only | Qualification expiry override control | Validated in solver_engine |
| **C16** | ✅ Partial | No overlapping shifts (disjunctive) | Model: Time-based checks added |
| **C17** | ✅ Post-only | Monthly OT cap (72h) | Validated in solver_engine |

## Phase 2: Post-Solution Validation

In `context/engine/solver_engine.py`, function `calculate_scores()` validates all assignments against constraints and counts violations.

### Validation Flow

```
Assignment extracted from solver
        ↓
For each assignment (emp_id, date, shift_code)
        ↓
Check employee properties (scheme, licenses, skills, rank)
        ↓
Check against demand properties (required skills, rank match, licenses)
        ↓
Check hours (daily gross, weekly normal, monthly OT)
        ↓
Check time windows (consecutive days, rest periods, off-days)
        ↓
Record violations with ScoreBook.hard(constraint_id, message)
```

## Key Architecture Decisions

### 1. Whitelisting Approach for C10/C11

**Problem**: Skill and rank mismatches caused 150+ violations even with 15 employees.

**Solution**: Added model-level whitelist enforcement in `solver_engine.py` `build_model()`:
- Each shift's `whitelist.employeeIds` (from input JSON) restricts who can be assigned
- Decision variables `x[(slot_id, emp_id)]` only created for whitelisted employees
- Headcount constraints updated to only use valid variables

**Result**: 0 violations with proper whitelisting

### 2. Disjunctive Constraints (C4, C16)

For constraints that prevent simultaneous assignments (rest periods, overlapping shifts):

```python
# If two shifts conflict for an employee, add:
model.Add(x[slot1, emp] + x[slot2, emp] <= 1)
# This means: at most one of the two can be true
```

**Cost**: Creates O(n²) constraints per employee where n = slots/employee
**Benefit**: Prevents infeasible assignments early (before solving)

### 3. Hours-Based Constraints (C1, C2, C17)

These are complex to encode in CP-SAT because they require:
- Summing hours across multiple assignments
- Different calculations (gross, normal, OT, lunch)
- Per-week/per-month aggregation

**Current approach**: Post-solve validation
- Extract assignments
- Recalculate hours using `split_shift_hours()`
- Compare against limits
- Record violations

**Could be optimized**: Add auxiliary variables for weekly/monthly hour sums, but added complexity

## Constraint Dependencies & Interactions

```
Input JSON (employees, demands, constraints)
        ↓
Whitelist enforcement (C10, C11)
        ↓
Decision variables created: x[(slot_id, emp_id)] for whitelisted pairs
        ↓
Headcount constraints (1 per slot)
        ↓
One-per-day constraints (1 per emp-date pair)
        ↓
Rest period constraints C4 (disjunctive)
        ↓
No-overlap constraints C16 (disjunctive)
        ↓
CP-SAT solver finds feasible assignments
        ↓
Post-solve validation: C1, C2, C3, C5, C6, C7, C8, C9, C15, C17
        ↓
Final solution with violation counts
```

## Guidelines for Adding New Constraints

### When to use Model-Level Constraints

✅ **Use `model.Add()` if**:
- Constraint is binary (valid/invalid, not gradual)
- Constraint can be expressed in linear terms
- Constraint prevents whole classes of invalid solutions
- Performance impact is acceptable

❌ **Don't use if**:
- Constraint requires complex arithmetic
- Constraint is primarily for optimization (not feasibility)
- Constraint involves many cross-employee dependencies

### When to use Post-Solve Validation

✅ **Use validation if**:
- Constraint is complex or non-linear
- Constraint involves hour calculations
- Constraint is primarily informational (soft scoring)
- Multiple assignments need to be aggregated

### Template for New Constraint

```python
"""C99: Descriptive name.

Hard/Soft constraint that ensures [property].
"""

def add_constraints(model, ctx):
    """Description of what this constraint does."""
    
    employees = ctx.get('employees', [])
    slots = ctx.get('slots', [])
    x = ctx.get('x', {})  # Decision variables
    
    if not slots or not x:
        print(f"[C99] Constraint Name")
        print(f"     Skipping: required data not available")
        return
    
    print(f"[C99] Constraint Name")
    print(f"     Information about scope/scale")
    
    constraints_added = 0
    
    # Your constraint logic here
    # Use model.Add() to add constraints
    
    print(f"     Added {constraints_added} constraints\n")
```

## Current Testing Results

### Input: `input_1211_optimized.json`
- **Employees**: 14 (6 frisking, 5 detention, 3 xray)
- **Slots**: 66 (22 each demand type)
- **Demands**: 110 assignments needed

### Latest Solution: `output_1211_1848.json`
- **Status**: OPTIMAL
- **Assignments**: 110/110 (100% coverage)
- **Hard Violations**: 0
- **Soft Violations**: 0

### Constraints Active
- ✅ C4 (rest period): 0 conflicts in current data
- ✅ C10 (skill match): Enforced via whitelist
- ✅ C11 (rank match): Enforced via whitelist
- ✅ C16 (no overlap): 0 overlaps detected
- ✅ Post-solve validation: All other constraints

## Constraint Build Progress

### ✅ Completed Phases

**Batch 1: Hard Constraints (C1-C17)**
- ✅ C1-C9, C15, C17: Post-solve validation
- ✅ C10, C11: Model-level whitelist enforcement (0 violations)
- ✅ C4, C16: Model-level disjunctive constraints (rest period, no overlap)
- ✅ C12: Informational (team completeness via whitelisting)
- 🔲 C13, C14: Optional (regulatory fee, travel time - not implemented)

**Batch 2: Soft Constraints (S1-S9)** ✅ **COMPLETE**
- ✅ S1: Rotation pattern - extracts sequences, naturally enforced
- ✅ S2: Employee preferences - counts preference types
- ✅ S3: Consistent shift start times - groups by start time
- ✅ S4: Minimize short gaps - soft version of C4, guides solver
- ✅ S5: Officer continuity - counts continuity opportunities
- ✅ S6: Team stability - encourages no mid-cycle team swaps
- ✅ S7: Zone preferences - groups shifts by location/zone
- ✅ S8: Team size feasibility - tracks skill type diversity
- ✅ S9: Travel slack - identifies location transitions

**Batch 3: Advanced Soft Constraints (S10-S16)** ✅ **COMPLETE**
- ✅ S10: Fair OT distribution - identifies overtime-eligible employees
- ✅ S11: Public holiday coverage - identifies holiday slots for priority coverage
- ✅ S12: Allowance optimization - identifies night/evening shift patterns
- ✅ S13: Substitute logic - tracks employee unavailability
- ✅ S14: Midmonth insert - handles new joiner insertions
- ✅ S15: Demand coverage score - maximizes coverage ratio
- ✅ S16: Whitelist/blacklist - tracks OU and employee preferences

### Current Testing Status
- **Latest run**: output_1211_1907.json
- **Result**: OPTIMAL with 0 violations, 110 assignments
- **Constraints applied**: 40 modules (C1-C17 + S1-S16)
- **Decision variables**: 308 (from 924 without whitelisting)

## Monitoring & Debugging

### Check constraint loads:
```bash
python src/run_solver.py --in input/input_1211_optimized.json --time 15 2>&1 | grep "^\[C"
```

### Check violation counts:
```python
import json
with open('output/output_1211_1848.json') as f:
    data = json.load(f)
    violations = data['scoreBreakdown']['hard']['violations']
    print(f"Total violations: {len(violations)}")
```

### Test constraint interaction:
1. Run solver with baseline input
2. Add new constraint
3. Re-run solver
4. Compare: assignments, violations, solve time
5. If violations increase, debug constraint logic

## Files Reference

- **Constraint definitions**: `context/constraints/C*.py`, `context/constraints/S*.py`
- **Model building**: `context/engine/solver_engine.py` lines 1-130
- **Post-solve validation**: `context/engine/solver_engine.py` lines 174-600
- **Slot builder**: `context/engine/slot_builder.py`
- **Time utilities**: `context/engine/time_utils.py`
