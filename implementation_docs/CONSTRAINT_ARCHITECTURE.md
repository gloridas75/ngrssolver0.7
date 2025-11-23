# NGRS Solver: Constraint Architecture & Configuration

## Overview

The NGRS Solver uses a **hybrid constraint model**:
- **Input-driven parameters** (`constraintList`, `solverScoreConfig`) configure **existing constraint logic**
- **Hard-coded constraint implementations** in `context/constraints/*.py` define the actual solver behavior
- The solver does NOT dynamically generate constraints from input JSON—it reads parameters that modify pre-built constraint modules

---

## Table of Contents

1. [Data Flow](#data-flow)
2. [Constraint List Handling](#constraint-list-handling)
3. [Solver Score Config](#solver-score-config)
4. [Individual Constraint Reference](#individual-constraint-reference)
5. [How to Modify Constraints](#how-to-modify-constraints)
6. [Current Gaps & Limitations](#current-gaps--limitations)

---

## Data Flow

### Complete Request Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. INPUT JSON (input_1211_optimized.json)                       │
│    - constraintList: [...]                                      │
│    - solverScoreConfig: {...}                                   │
│    - employees, demandItems, etc.                               │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. API SERVER (src/api_server.py)                               │
│    - POST /solve endpoint receives JSON                         │
│    - Calls load_input(input_json)                               │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. DATA LOADER (context/engine/data_loader.py)                  │
│    - Parses JSON into ctx dict                                  │
│    - ctx['constraintList'] = input JSON constraintList          │
│    - ctx['solverScoreConfig'] = input JSON solverScoreConfig    │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. SOLVER ENGINE (context/engine/solver_engine.py)              │
│    - solve(ctx) function:                                       │
│      - build_model(ctx) → creates CP-SAT model                  │
│      - apply_constraints(model, ctx) → loads constraint modules │
│      - solver.Solve(model) → runs optimization                  │
│      - calculate_scores(ctx, assignments)                       │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. CONSTRAINT MODULES (context/constraints/C*.py, S*.py)        │
│    - Each reads ctx['constraintList'] to find its config        │
│    - Extracts parameters (minRestMinutes, maxWeeklyHours, etc.) │
│    - Applies constraint logic using those parameters            │
│    - Hard (C): Blocks infeasible assignments                    │
│    - Soft (S): Penalizes violations                             │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. SCORE BOOK (context/engine/score_helpers.py)                 │
│    - Initialized with ctx['solverScoreConfig']                  │
│    - Records violations with weighted penalties                 │
│    - Calculates final hard/soft scores                          │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. OUTPUT (src/output_builder.py)                               │
│    - Builds response with:                                      │
│      - solverRun.status (OPTIMAL/FEASIBLE/INFEASIBLE)           │
│      - score.hard, score.soft                                   │
│      - assignments, violations                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Constraint List Handling

### Input Format

```json
"constraintList": [
  {
    "id": "apgdMinRestBetweenShifts",
    "enforcement": "hard",
    "params": {"minRestMinutes": 660}
  },
  {
    "id": "oneShiftPerDay",
    "enforcement": "hard"
  },
  {
    "id": "teamFirstRostering",
    "enforcement": "soft"
  }
]
```

### How Each Constraint Module Uses This

#### Example 1: C4_rest_period.py (Hard Constraint)

**Code in constraint file:**
```python
def add_constraints(model, ctx):
    constraint_list = ctx.get('constraintList', [])
    
    # Find the specific constraint configuration
    min_rest_minutes = 480  # Default: 8 hours
    for constraint in constraint_list:
        if constraint.get('id') == 'apgdMinRestBetweenShifts':
            min_rest_minutes = constraint.get('params', {}).get('minRestMinutes', 480)
            break
    
    min_rest_hours = min_rest_minutes / 60
    print(f"[C4] Minimum rest required: {min_rest_hours:.1f} hours ({min_rest_minutes} minutes)")
    
    # ... rest of constraint logic using min_rest_minutes
```

**What happens with your input:**
- Your JSON has `"minRestMinutes": 660` (11 hours)
- Solver reads this value and **enforces 11-hour rest minimum** between shifts
- If any assignment violates this → **solver rejects it** (hard constraint)

#### Example 2: S1_rotation_pattern.py (Soft Constraint)

**Code in constraint file:**
```python
def add_constraints(model, ctx):
    constraint_list = ctx.get('constraintList', [])
    
    # Check if this soft constraint is enabled
    constraint_enabled = False
    for constraint in constraint_list:
        if constraint.get('id') == 'teamFirstRostering':
            constraint_enabled = (constraint.get('enforcement') != 'disabled')
            break
    
    if not constraint_enabled:
        return  # Skip this constraint if disabled
    
    # ... apply soft constraint logic
```

**What happens with your input:**
- Your JSON has `"id": "teamFirstRostering", "enforcement": "soft"`
- Solver **enables this soft constraint**
- If assignments violate team-first preference → **adds penalty to score** (doesn't block)

---

### Constraint ID Reference

| Constraint ID | Type | File | Parameters | What It Does |
|---------------|------|------|------------|--------------|
| `apgdMinRestBetweenShifts` | Hard | C4_rest_period.py | `minRestMinutes` | Minimum rest between consecutive shifts |
| `oneShiftPerDay` | Hard | C3_consecutive_days.py | (none) | Max 1 shift per employee per day |
| `slotHeadcount` | Hard | C12_team_completeness.py | (none) | Fill all required slot positions |
| `momWeeklyHoursCap44h` | Hard | C2_mom_weekly_hours.py | `maxWeeklyHours` | Weekly hour cap for employees |
| `teamFirstRostering` | Soft | S1_rotation_pattern.py | (none) | Prefer keeping teams together |
| `minimizeGapsBetweenAssignedShifts` | Soft | S4_min_short_gaps.py | (none) | Minimize time gaps between shifts |
| `parentalCare` | Soft | S2_preferences.py | (none) | Honor employee preferences |
| `offDayConsecutive` | Hard | C5_offday_rules.py | (none) | Ensure consecutive off days |
| `skillMatch` | Hard | C10_skill_role_match.py | (none) | Verify required skills present |
| `licenseValidity` | Hard | C7_license_validity.py | (none) | Check license expiry dates |

---

## Solver Score Config

### Input Format

```json
"solverScoreConfig": {
  "teamFirstRostering": 5,
  "minimizeGapsBetweenAssignedShifts": 1
}
```

### How It's Used

**In solver_engine.py (line 216):**
```python
def calculate_scores(ctx, assignments):
    # Initialize ScoreBook with solver config weights
    score_config = ctx.get('solverScoreConfig', {})
    score_book = ScoreBook(score_config)  # Passes weights to score tracker
    
    # When violations are recorded:
    score_book.soft('teamFirstRostering', 'message', base_penalty=100)
    # Applied penalty = base_penalty * score_config['teamFirstRostering']
    #                 = 100 * 5 = 500 points
```

### Weighting Logic

Your `solverScoreConfig`:
```json
{
  "teamFirstRostering": 5,              // 5x multiplier
  "minimizeGapsBetweenAssignedShifts": 1 // 1x multiplier (default)
}
```

**Score Calculation:**
- Base violation penalty: varies by constraint (typically 1-100)
- Weight from solverScoreConfig: your multiplier
- **Final penalty = base × weight**

**Example:**
- Constraint: `teamFirstRostering`
- Base penalty: 50 points per violation
- Your weight: 5
- **Final score = 50 × 5 = 250 points penalty**

If weight is missing from `solverScoreConfig`:
- Default weight = 1
- Violation = 50 points (no multiplier)

---

## Individual Constraint Reference

### Hard Constraints (Blocking)

#### C1: MOM Daily Hours
- **File:** `C1_mom_daily_hours.py`
- **Reads from:** constraintList (not used currently)
- **Logic:** Validates daily hours don't exceed MOM regulations
- **Parameters:** (none specified in your JSON)

#### C2: MOM Weekly Hours Cap (44h)
- **File:** `C2_mom_weekly_hours.py`
- **Reads from:** constraintList `momWeeklyHoursCap44h.params.maxWeeklyHours`
- **Your config:** `"maxWeeklyHours": 44`
- **Logic:** Enforces max 44 hours per week per employee
- **Enforcement:** Hard (blocks assignments exceeding cap)

#### C3: Consecutive Days
- **File:** `C3_consecutive_days.py`
- **Reads from:** constraintList (not used)
- **Logic:** Enforces shift rotation patterns (e.g., max 5 consecutive work days)
- **Parameters:** (none)

#### C4: Minimum Rest Between Shifts
- **File:** `C4_rest_period.py`
- **Reads from:** constraintList `apgdMinRestBetweenShifts.params.minRestMinutes`
- **Your config:** `"minRestMinutes": 660` (11 hours)
- **Logic:** Enforces minimum rest between consecutive shifts
- **Enforcement:** Hard (blocks assignments violating rest requirement)

#### C5: Off-Day Rules
- **File:** `C5_offday_rules.py`
- **Reads from:** demandItems rotation patterns
- **Logic:** Respects rotation sequences (e.g., ["D","D","D","D","D","O","O"])
- **Enforcement:** Hard

#### C7-C17: Additional Hard Constraints
- License validity checks
- Skill matching
- Team completeness
- Travel time limits
- Gender balance requirements
- No shift overlaps
- OT monthly caps

### Soft Constraints (Scoring)

#### S1: Rotation Pattern Preference
- **File:** `S1_rotation_pattern.py`
- **Reads from:** constraintList `teamFirstRostering`
- **Scoring:** 5x multiplier (from your solverScoreConfig)
- **Logic:** Prefer keeping employees in their assigned teams
- **Enforcement:** Soft (penalties if violated)

#### S2: Employee Preferences
- **File:** `S2_preferences.py`
- **Reads from:** employees.preferences
- **Logic:** Honor employee date/shift preferences
- **Enforcement:** Soft

#### S3-S9: Additional Soft Constraints
- Consistent shift start times
- Minimize short gaps between shifts
- Officer continuity
- Minimize shift changes within teams
- Zone preferences
- Team size feasibility
- Travel slack time

---

## How to Modify Constraints

### Scenario 1: Change a Parameter Value

**Goal:** Increase max weekly hours from 44 to 45

**Your input JSON:**
```json
"constraintList": [
  {
    "id": "momWeeklyHoursCap44h",
    "enforcement": "hard",
    "params": {"maxWeeklyHours": 45}  // Changed from 44
  }
]
```

**What happens:**
1. Constraint module C2_mom_weekly_hours.py reads this
2. Extracts `maxWeeklyHours = 45`
3. Solver enforces 45-hour cap (instead of 44)

**No code changes needed** ✓

### Scenario 2: Disable a Constraint

**Goal:** Disable the minimum rest requirement

**Your input JSON:**
```json
"constraintList": [
  {
    "id": "apgdMinRestBetweenShifts",
    "enforcement": "disabled",  // Changed from "hard"
    "params": {"minRestMinutes": 660}
  }
]
```

**What happens:**
1. Constraint module checks: `if enforcement == 'disabled': return`
2. Constraint is skipped entirely
3. Solver allows shifts with any rest period

**Requirement:** Constraint module must check enforcement status (not all do currently)

### Scenario 3: Change Soft Constraint Weight

**Goal:** Make team-first rostering 10x more important

**Your input JSON:**
```json
"solverScoreConfig": {
  "teamFirstRostering": 10,  // Increased from 5
  "minimizeGapsBetweenAssignedShifts": 1
}
```

**What happens:**
1. Each team-first violation is penalized 10x more
2. Solver tries harder to keep teams together
3. May sacrifice other optimizations to satisfy this

**No code changes needed** ✓

### Scenario 4: Add a New Constraint Parameter

**Goal:** Add a new parameter to C4 (rest period)

**Step 1: Modify input JSON**
```json
{
  "id": "apgdMinRestBetweenShifts",
  "enforcement": "hard",
  "params": {
    "minRestMinutes": 660,
    "minRestBetweenNightShifts": 720  // New parameter
  }
}
```

**Step 2: Update C4_rest_period.py**
```python
def add_constraints(model, ctx):
    constraint_list = ctx.get('constraintList', [])
    
    for constraint in constraint_list:
        if constraint.get('id') == 'apgdMinRestBetweenShifts':
            params = constraint.get('params', {})
            min_rest_minutes = params.get('minRestMinutes', 480)
            min_rest_night = params.get('minRestBetweenNightShifts', 720)  # NEW
            break
    
    # Use both parameters in constraint logic
```

**Requirement:** Modify the constraint module code

---

## Current Gaps & Limitations

### Gap 1: Not All Constraints Read constraintList

**Issue:** Some constraint modules don't read from `constraintList`. They use hardcoded values instead.

**Example - C3_consecutive_days.py:**
```python
def add_constraints(model, ctx):
    # Reads from demandItems rotation patterns, NOT constraintList
    for demand in ctx.get('demandItems', []):
        for shift in demand['shifts']:
            rotation = shift.get('rotationSequence', [])  # Uses hardcoded pattern
            # Does NOT look for "consecutiveDaysMax" in constraintList
```

**Impact:** You can't modify consecutive day limits via `constraintList`

**Fix needed:** Update C3 to read from `constraintList`

### Gap 2: Enforcement Status Not Enforced Everywhere

**Issue:** Not all constraint modules check if `enforcement == 'disabled'`

**Example - C1_mom_daily_hours.py:**
```python
def add_constraints(model, ctx):
    # Doesn't check enforcement status
    # Always applies, even if disabled in constraintList
    # Hardcoded to always enforce
```

**Impact:** Can't disable constraints via `enforcement: 'disabled'`

**Fix needed:** Add enforcement checks to all hard constraints

### Gap 3: New Constraints Require Code Changes

**Issue:** To add a new constraint, must:
1. Create new Python file in `context/constraints/`
2. Implement `add_constraints(model, ctx)` function
3. Deploy new code

**Impact:** Can't dynamically add constraints via input JSON

**Workaround:** Wrap in `enforcement: 'disabled'` if not needed

### Gap 4: solverScoreConfig Only Used for Post-Solution Scoring

**Issue:** `solverScoreConfig` weights violations AFTER solving, not during

**Impact:**
- Doesn't influence solver decision-making during optimization
- Only affects final score calculation
- Solver can't "prefer" constraint A over constraint B during search

**Fix needed:** Integrate score weights into objective function (advanced)

---

## Key Takeaways

### ✓ What You CAN Do via Input JSON

1. **Change constraint parameters:**
   - `minRestMinutes: 660` → min rest becomes 11 hours
   - `maxWeeklyHours: 45` → max hours becomes 45
   - (For parameters your constraint modules read)

2. **Weight soft constraints:**
   - `"solverScoreConfig": {"teamFirstRostering": 5}` → 5x penalty multiplier

3. **Specify enforcement:**
   - `"enforcement": "hard"` → must satisfy
   - `"enforcement": "soft"` → penalize if violated
   - `"enforcement": "disabled"` → skip constraint (if module supports it)

### ✗ What You CANNOT Do (Requires Code Changes)

1. Add entirely new constraint types
2. Change constraint logic/algorithms
3. Disable constraints not checked for enforcement status
4. Modify constraints not reading from `constraintList`

### Configuration Best Practices

1. **Always list all constraints you want:**
   ```json
   "constraintList": [
     {"id": "...", "enforcement": "hard", "params": {...}},
     {"id": "...", "enforcement": "soft"}
   ]
   ```

2. **Set sensible parameters:**
   - `minRestMinutes`: 480-660 (8-11 hours)
   - `maxWeeklyHours`: 40-48 (regulatory limits)
   - Use realistic values based on your business rules

3. **Use solverScoreConfig strategically:**
   - Weight constraints by importance
   - Higher weight = solver prioritizes more
   - Balance all constraints (too high weights can cause infeasibility)

4. **Test parameter changes:**
   - Small adjustments can have large effects
   - Monitor solver output for feasibility
   - Compare scores across runs

---

## Architecture Diagram

```
INPUT JSON
    │
    ├─ constraintList[]
    │     │
    │     ├─ id: "constraint_id"
    │     ├─ enforcement: "hard|soft|disabled"
    │     └─ params: { custom_params }
    │           │
    │           ↓
    │     CONSTRAINT MODULES (context/constraints/*.py)
    │           │
    │           ├─ Read: ctx['constraintList']
    │           ├─ Extract: params for THIS constraint
    │           ├─ Apply: constraint logic using params
    │           └─ Add: constraints to CP-SAT model
    │
    ├─ solverScoreConfig: { weight_map }
    │     │
    │     ↓
    │ SCORE BOOK (score_helpers.py)
    │     │
    │     ├─ Load: solverScoreConfig weights
    │     ├─ Record: violations with penalties
    │     └─ Calculate: final hard/soft scores
    │
    └─ other fields (employees, demandItems, etc.)
          │
          ↓
       CP-SAT SOLVER
          │
          ├─ Decision: assignments
          ├─ Objective: minimize violations
          └─ Constraints: all added by modules
          │
          ↓
       OUTPUT
          │
          ├─ solverRun.status
          ├─ score.hard / score.soft
          ├─ assignments
          └─ violations
```

---

## See Also

- `context/engine/solver_engine.py` - Main solve loop
- `context/constraints/` - Individual constraint implementations
- `context/engine/score_helpers.py` - Scoring logic
- `API_DOCUMENTATION.md` - Input/output format specification
