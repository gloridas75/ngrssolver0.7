# CP-SAT Understanding & Application in NGRS Solver

**Document Purpose:** Explain how Google OR-Tools CP-SAT model works and its specific application in the NGRS duty rostering solver.

**Audience:** Developers, AI agents, and constraint engineers working on NGRS.

---

## Table of Contents

1. [What is CP-SAT?](#what-is-cp-sat)
2. [Core Concepts](#core-concepts)
3. [How CP-SAT Solves Problems](#how-cp-sat-solves-problems)
4. [NGRS Application Architecture](#ngrs-application-architecture)
5. [Decision Variables in NGRS](#decision-variables-in-ngrs)
6. [Hard Constraints in CP-SAT](#hard-constraints-in-cp-sat)
7. [Soft Constraints & Optimization](#soft-constraints--optimization)
8. [NGRS Solver Workflow](#ngrs-solver-workflow)
9. [Common Patterns & Examples](#common-patterns--examples)
10. [Performance Considerations](#performance-considerations)

---

## What is CP-SAT?

### Definition

**CP-SAT** = **Constraint Programming - Satisfiability** (hybrid solver)

From Google OR-Tools library: A high-performance constraint programming solver that combines:
- **Constraint Propagation** (classical CP techniques)
- **SAT Solving** (satisfiability algorithm)
- **Linear Relaxation** (LP-based bounds)

### Key Characteristics

| Feature | Description |
|---------|-------------|
| **Problem Type** | Combinatorial optimization (discrete variables, constraints) |
| **Variables** | Integer, Boolean (0/1), or continuous |
| **Constraints** | Linear, reified (conditional), disjunctive |
| **Objective** | Maximize or minimize (optional) |
| **Time Limit** | Configurable (default: unlimited) |
| **Solution Quality** | OPTIMAL, FEASIBLE, or INFEASIBLE |

### Why CP-SAT for Rostering?

1. **Handles discrete decisions:** Each shift slot is assigned to 0 or 1 employee
2. **Encodes complex rules:** Hours limits, rest periods, qualifications all expressible as constraints
3. **Proof of infeasibility:** Can definitively say "no solution exists" if constraints conflict
4. **Optimizes under constraints:** Finds best solution that respects ALL hard constraints

---

## Core Concepts

### 1. Decision Variables

**Definition:** Variables representing unknown decisions the solver will determine.

**In NGRS Rostering:**

```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()

# Decision variable: Can employee E_001 be assigned to slot S_001?
x_001_001 = model.NewBoolVar(name="x[S_001][E_001]")
# Domain: {0, 1}
# 0 = not assigned
# 1 = assigned
```

**Characteristics:**
- Each variable has a **domain** (range of possible values)
- Boolean vars: domain = {0, 1}
- Integer vars: domain = {min, ..., max}
- Solver determines final value when solving

### 2. Constraints

**Definition:** Rules that must be satisfied by the final solution.

**Types:**

#### Linear Constraints
```python
# Sum must equal headcount
# x[slot][emp1] + x[slot][emp2] + ... = headcount
model.Add(sum([x[(slot, emp) for emp in employees]) == slot.headcount)

# Weekly hours must not exceed limit
# (normal_hours[slot1] * x[slot1][emp]) + ... <= 44 hours
model.Add(sum(normal_hours[s] * x[(s, emp)] for s in week_slots) <= 440)
# Note: × 10 for integer arithmetic
```

#### Disjunctive Constraints (Only One Can Be True)
```python
# Employee cannot work two overlapping shifts
# x[slot_A][emp] = 1 AND x[slot_B][emp] = 1 is forbidden
# Implemented: AddNoOverlap() or manual disjunction
model.AddNoOverlap([interval_A, interval_B])
```

#### Reified Constraints (Conditional)
```python
# If x[slot][emp] = 1, then employee must have license
# model.Add(x[slot][emp] == 1).OnlyEnforceIf(has_license[emp])
```

### 3. Objective Function

**Definition:** Optimization goal - what to maximize or minimize.

**In NGRS:**

```python
# Maximize total assignments (feasibility)
all_vars = list(x.values())
model.Maximize(sum(all_vars))

# This means: "Find assignment that fills as many slots as possible"
```

**Later (soft constraints):**
```python
# Minimize soft constraint penalties (quality)
# model.Minimize(soft_penalty_total)
```

### 4. Solution States

When solver returns, status is one of:

| Status | Meaning | Hard Constraints | Solution Quality |
|--------|---------|------------------|------------------|
| **OPTIMAL** | Best possible solution found | ✅ All satisfied | 100% (or provably best) |
| **FEASIBLE** | Valid solution found, but maybe not best | ✅ All satisfied | Good (within time limit) |
| **INFEASIBLE** | No solution satisfies constraints | ❌ Conflict detected | N/A - no solution |
| **UNKNOWN** | Time limit reached, no solution yet | Unknown | Incomplete search |

---

## How CP-SAT Solves Problems

### Solving Algorithm (High-Level)

```
1. MODEL SETUP PHASE
   ├─ Create variables (domains)
   ├─ Add constraints (propagate immediately)
   └─ Set objective (optional)

2. PREPROCESSING
   ├─ Constraint simplification
   ├─ Variable elimination
   ├─ Bound tightening
   └─ Feasibility check (early infeasibility detection)

3. SEARCH PHASE (Time-limited)
   ├─ Branch-and-bound search
   ├─ Constraint propagation at each branch
   ├─ Heuristics to find feasible solutions quickly
   └─ Prune branches that can't improve objective

4. SOLUTION REPORTING
   └─ Return best solution found + status
```

### Constraint Propagation (The Magic)

**Example:**
```python
model.Add(x[slot1][emp] + x[slot2][emp] <= 1)  # Can't work both slots
model.Add(x[slot1][emp] + x[slot3][emp] <= 1)  # Can't work both slots
model.Add(x[slot2][emp] + x[slot3][emp] <= 1)  # Can't work both slots
# If solver tries x[slot1][emp]=1, it propagates:
#   -> x[slot2][emp] must be 0
#   -> x[slot3][emp] must be 0
#   -> This prunes entire branches of search space
```

**Result:** Solver explores only relevant combinations → Fast solution!

---

## NGRS Application Architecture

### The NGRS Rostering Problem Formulation

**What are we solving?**
- **Goal:** Assign employees to shift slots
- **Constraint:** Respect labor laws, qualifications, preferences
- **Optimize:** Maximize coverage, fairness, business preferences

### Mathematical Formulation

```
Maximize:   Σ x[s,e]  (total assignments)
            + soft_penalties scoring

Subject to:

HARD CONSTRAINTS:
  C1: ∀(e,w) : Σ(normal_hours[s] * x[s,e] for s in week) ≤ 44h
  C2: ∀(e,w) : Σ(ot_hours[s] * x[s,e] for s in week) ≤ 72h
  C4: ∀(s1,s2,e) : rest_between(s1,s2) ≥ 11h OR ¬(x[s1,e] ∧ x[s2,e])
  C7: ∀(s,e) : IF x[s,e]=1 THEN e.has_license(demand[s].required_license)
  C11: ∀(s,e) : IF x[s,e]=1 THEN e.rank == demand[s].product_type
  ... (15 more hard constraints)

SOFT CONSTRAINTS:
  S1-S16: Scored violations, minimized in objective

VARIABLES:
  x[s,e] ∈ {0,1}  ∀ slot s, employee e
  (with whitelist filtering)
```

---

## Decision Variables in NGRS

### Structure: x[(slot_id, employee_id)]

```python
x = {}  # Dictionary of all decision variables

# Example structure after model building:
x = {
    ("D_FRISKING-2025-11-01-D-uuid1", "ALICE_001"): BoolVar(...),
    ("D_FRISKING-2025-11-01-D-uuid1", "BOB_001"): BoolVar(...),
    ("D_FRISKING-2025-11-01-D-uuid1", "CAROL_001"): BoolVar(...),
    ("D_FRISKING-2025-11-02-D-uuid2", "ALICE_001"): BoolVar(...),
    ...
}
```

### Variable Creation (Whitelist Filtering)

```python
# Built in solver_engine.build_model()

for slot in slots:
    for emp in employees:
        emp_id = emp.get('employeeId')
        
        # Check if employee is whitelisted for this slot
        whitelist = slot.whitelist
        is_whitelisted = True
        
        if any(whitelist.get(k) for k in ['employeeIds', 'teamIds', 'ouIds']):
            is_whitelisted = False
            
            # Check employee whitelist
            if whitelist.get('employeeIds') and emp_id in whitelist['employeeIds']:
                is_whitelisted = True
            # Check team whitelist
            elif whitelist.get('teamIds') and emp.get('teamId') in whitelist['teamIds']:
                is_whitelisted = True
            # Check OU whitelist
            elif whitelist.get('ouIds') and emp.get('ouId') in whitelist['ouIds']:
                is_whitelisted = True
        
        # Only create decision variable if whitelisted
        if is_whitelisted:
            var_name = f"x[{slot.slot_id}][{emp_id}]"
            x[(slot.slot_id, emp_id)] = model.NewBoolVar(var_name)
```

**Why Whitelist at Variable Level?**
- Reduces variable count (e.g., 1M → 100K variables)
- Solver only searches relevant combinations
- C14 (Whitelist/Blacklist) partially enforced at creation time

### Total Variables in NGRS

**Estimation for typical month:**
```
Slots = Demands × Days × Headcount
      = 8 demands × 22 workdays × 1.5 avg headcount
      = ~264 slots

Employees = 50

Without Whitelist: 264 × 50 = 13,200 variables
With Whitelist: 264 × 50 × 20% = 2,640 variables (80% pruned)

Solver much faster with whitelist!
```

---

## Hard Constraints in CP-SAT

### How Hard Constraints Work

**Hard Constraint = `model.Add(...)`**

```python
# Example: Weekly hours ≤ 44h (C2)
def add_constraints(model, ctx):
    slots = ctx.get('slots', [])
    x = ctx.get('x', {})
    employees = ctx.get('employees', [])
    
    # Group slots by (employee, week)
    slots_by_emp_week = defaultdict(list)
    for slot in slots:
        emp_id = ...
        week = slot.date.isocalendar()[1]  # ISO week
        slots_by_emp_week[(emp_id, week)].append(slot)
    
    # Add constraint: sum of normal hours ≤ 440 (×10 scaling)
    for (emp_id, week), week_slots in slots_by_emp_week.items():
        # Collect normal hours for each slot
        normal_hour_terms = []
        for slot in week_slots:
            if (slot.slot_id, emp_id) in x:
                var = x[(slot.slot_id, emp_id)]
                normal_hours_scaled = int(slot.normal_hours * 10)
                normal_hour_terms.append(normal_hours_scaled * var)
        
        if normal_hour_terms:
            # Add constraint to model
            model.Add(sum(normal_hour_terms) <= 440)  # 44h × 10
```

### Integer Scaling (Important!)

**Why scale by 10?**
- CP-SAT requires integer coefficients
- Cannot use floats like 8.5 directly
- Solution: multiply everything by 10

**Example:**
```
Unscaled: 8.5h + 8.3h + 3.2h = 20h limit
Scaled:   85 + 83 + 32 = 200 (all integers)
Result:   Same constraint, solver-compatible
```

### Violation Enforcement

**Hard constraints BLOCK assignments if violated:**

```python
# C7: License Validity - employee must have required license
for slot in slots:
    required_quals = slot.required_qualifications
    for emp in employees:
        emp_id = emp.get('employeeId')
        emp_licenses = {lic['code']: lic['expiryDate'] for lic in emp.get('licenses', [])}
        
        # Check if employee has all required qualifications
        has_valid_quals = True
        for qual_code in required_quals:
            if qual_code not in emp_licenses:
                has_valid_quals = False
                break
            expiry_date = emp_licenses[qual_code]
            if slot.date > expiry_date:  # Expired
                has_valid_quals = False
                break
        
        # If not qualified, FORCE assignment to 0
        if not has_valid_quals and required_quals:
            if (slot.slot_id, emp_id) in x:
                var = x[(slot.slot_id, emp_id)]
                model.Add(var == 0)  # Cannot assign this person to this slot
```

**Result:**
- If 10 people are needed but only 8 qualify → INFEASIBLE
- Solver returns status = INFEASIBLE
- No partial/invalid solution returned

---

## Soft Constraints & Optimization

### Soft Constraints = Scoring/Penalties

Unlike hard constraints, soft constraints allow violations but **penalize** them in the objective:

```python
# Pseudo-code for soft constraint scoring
soft_penalty = 0

# S1: Rotation Pattern Compliance
for emp_id, assignments in group_by_employee(assignments):
    pattern_violations = count_pattern_deviations(emp_id, assignments)
    weight = solverScoreConfig["S1_rotation_pattern"]  # e.g., 2
    soft_penalty += pattern_violations * weight

# S5: Officer Continuity
for (site, date), officers in group_by_site_date(assignments):
    continuity_violations = count_officer_changes(officers, date)
    weight = solverScoreConfig["S5_officer_continuity"]  # e.g., 4
    soft_penalty += continuity_violations * weight

# ... (S2-S16 similar)

# Final objective (AFTER hard constraints satisfied)
model.Minimize(soft_penalty)
```

### Soft Constraint in CP-SAT

```python
# In solver_engine.solve()
# After hard constraints are added...

# Build soft objective
soft_objective_terms = []

for constraint_id, weight in solverScoreConfig.items():
    penalty = calculate_penalty(constraint_id, assignments)
    soft_objective_terms.append(weight * penalty)

if soft_objective_terms:
    model.Minimize(sum(soft_objective_terms))

# Solve
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Can inspect soft violations from assignments
    score_breakdown = calculate_soft_breakdown(assignments)
```

---

## NGRS Solver Workflow

### End-to-End Flow with CP-SAT

```
INPUT: input.json (v0.50)
  ↓
LOAD & VALIDATE
  context/engine/data_loader.load_input()
  ↓
EXPAND DEMANDS → SLOTS
  context/engine/slot_builder.build_slots()
  Output: ~264 slots (date, shift, site, role, headcount)
  ↓
BUILD CP-SAT MODEL
  context/engine/solver_engine.build_model(ctx)
  - Create x[(slot, emp)] boolean variables
  - Apply whitelist filtering
  - Add basic constraints (headcount, one-per-day)
  - Set objective: Maximize assignments
  ↓
APPLY HARD CONSTRAINTS (C1-C17)
  solver_engine.apply_constraints(model, ctx)
  Dynamically load context/constraints/C*.py
  Each module calls model.Add(...) for its rules
  ↓
APPLY SOFT CONSTRAINTS (S1-S16)
  Same apply_constraints() call
  Soft constraints calculated as penalties
  ↓
SOLVE (5-600 second time limit)
  solver = cp_model.CpSolver()
  status = solver.Solve(model)
  ↓
EXTRACT SOLUTION
  For each (slot, emp) where solver.Value(x[(slot, emp)]) == 1:
    Create assignment record
  ↓
CALCULATE SCORES
  Hard violations: 0 (if OPTIMAL/FEASIBLE)
  Soft violations: From solution validation
  ↓
BUILD OUTPUT JSON
  src/output_builder.py
  - assignments[]
  - score: {overall, hard, soft}
  - scoreBreakdown: {hard: {violations}, soft: {details}}
  ↓
OUTPUT: output.json (v0.50)
```

---

## Common Patterns & Examples

### Pattern 1: Simple Capacity Constraint

**Rule:** Each slot must have exactly `headcount` assignments

```python
# solver_engine.build_model()
for slot in slots:
    slot_assignments = [x[(slot.slot_id, emp.get('employeeId'))] 
                       for emp in employees 
                       if (slot.slot_id, emp.get('employeeId')) in x]
    if slot_assignments:
        model.Add(sum(slot_assignments) == slot.headcount)
```

**CP-SAT:** Linear constraint, very fast to solve.

### Pattern 2: Employee Availability (License Check)

**Rule:** Cannot assign to slot if no valid license

```python
# context/constraints/C7_license_validity.py
for slot in slots:
    required_quals = slot.required_qualifications
    for emp in employees:
        emp_id = emp.get('employeeId')
        
        if has_required_licenses(emp_id, required_quals, slot.date):
            continue  # OK
        else:
            # BLOCK this assignment
            if (slot.slot_id, emp_id) in x:
                var = x[(slot.slot_id, emp_id)]
                model.Add(var == 0)
```

**CP-SAT:** Reified constraint (conditional).

### Pattern 3: Weekly Hours Limit

**Rule:** Total normal hours per week ≤ 44h

```python
# context/constraints/C2_mom_weekly_hours.py
slots_by_emp_week = defaultdict(list)
for slot in slots:
    week = slot.date.isocalendar()[1]
    slots_by_emp_week[(emp_id, week)].append(slot)

for (emp_id, week), week_slots in slots_by_emp_week.items():
    normal_hour_terms = []
    for slot in week_slots:
        if (slot.slot_id, emp_id) in x:
            var = x[(slot.slot_id, emp_id)]
            normal_scaled = int(slot.normal_hours * 10)
            normal_hour_terms.append(normal_scaled * var)
    
    if normal_hour_terms:
        model.Add(sum(normal_hour_terms) <= 440)  # 44h * 10
```

**CP-SAT:** Linear constraint with aggregation.

### Pattern 4: No Overlapping Shifts

**Rule:** Employee cannot work two overlapping shifts on same day

```python
# solver_engine.build_model()
for emp_id in employee_ids:
    # Group slots by employee and date
    slots_by_date = defaultdict(list)
    for slot in slots:
        slots_by_date[(emp_id, slot.date)].append(slot)
    
    # At most 1 shift per day
    for (emp, date), date_slots in slots_by_date.items():
        emp_date_vars = [x[(slot.slot_id, emp_id)] 
                        for slot in date_slots 
                        if (slot.slot_id, emp_id) in x]
        if len(emp_date_vars) > 1:
            model.Add(sum(emp_date_vars) <= 1)
```

**CP-SAT:** Sum constraint (all true AND false).

---

## Performance Considerations

### 1. Variable Count Matters

| Variables | Typical Solve Time | Complexity |
|-----------|-------------------|-----------|
| < 5K | < 0.1s | Trivial |
| 5K - 50K | 0.1-5s | Easy-Medium |
| 50K - 500K | 5-60s | Medium-Hard |
| > 500K | 60s+ | Very Hard (needs tuning) |

**NGRS Target:** ~2K-5K variables (with whitelist) → 0.05-5s solve time

### 2. Constraint Count Matters

| Constraints | Impact | Solver Time |
|-------------|--------|-------------|
| < 1K | Minimal propagation | Fast |
| 1K - 10K | Good propagation | Medium |
| 10K - 100K | Strong constraints | May slow |
| > 100K | Constraint explosion | Very slow |

**NGRS Typical:** ~500-2K constraints → Good balance

### 3. Optimization: Whitelist at Variable Creation

**Without Whitelist:**
```
variables = 50 employees × 264 slots = 13,200 vars
solver explores: 2^13,200 ≈ infinity combinations
```

**With Whitelist (20% relevant):**
```
variables = 50 employees × 264 slots × 0.2 = 2,640 vars
solver explores: 2^2,640 ≈ still infinity, but much faster
```

### 4. Time Limit Strategy

```python
# src/run_solver.py or API
solver.parameters.max_time_in_seconds = max_seconds

# Strategy:
# - 5 seconds: Quick feedback for API
# - 30 seconds: Balanced quality
# - 300 seconds: High-quality overnight batch
```

---

## NGRS Solver Specific Implementation

### File-by-File Responsibility

| File | CP-SAT Role | Example |
|------|------------|---------|
| `solver_engine.build_model()` | Create variables, set objective | `x[(s,e)]` vars, Maximize assignments |
| `solver_engine.apply_constraints()` | Load & call constraint modules | Import C*.py files |
| `C*.py` modules | Add hard constraints | `model.Add(...)` |
| `S*.py` modules | Calculate soft penalties | Scoring logic |
| `output_builder.py` | Extract solution | Convert x values to assignments |

### Integer Arithmetic Requirement

**All coefficients in model.Add() must be integers:**

```python
# ❌ WRONG - float coefficient
model.Add(8.5 * x[(slot, emp)] + 3.2 * x[(slot2, emp)] <= 20.0)

# ✅ CORRECT - integer coefficient (scaled by 10)
model.Add(85 * x[(slot, emp)] + 32 * x[(slot2, emp)] <= 200)
```

### Decision Variable Access

**Reading solution values:**

```python
# After solver.Solve(model)
for (slot_id, emp_id), var in x.items():
    value = solver.Value(var)  # Returns 0 or 1 (for BoolVar)
    
    if value == 1:
        # This person is assigned to this slot
        assignments.append((slot_id, emp_id))
```

---

## Summary for NGRS Development

| Aspect | NGRS Implementation |
|--------|-------------------|
| **Model Type** | CP-SAT (BoolVar) |
| **Variables** | x[(slot_id, emp_id)] ∈ {0, 1} |
| **Hard Constraints** | model.Add() in C*.py files |
| **Soft Constraints** | Scoring penalties in S*.py files |
| **Objective** | Maximize assignments + minimize soft penalties |
| **Solution Status** | OPTIMAL / FEASIBLE / INFEASIBLE |
| **Typical Scale** | ~2K-5K variables, ~500-2K constraints, 0.05-30s |
| **Critical Pattern** | Whitelist at variable creation for efficiency |
| **Arithmetic** | All integer (scale floats by 10) |

---

**Next Steps for NGRS:**

1. ✅ Understand CP-SAT model structure
2. ✅ Understand NGRS decision variables (x[(slot, emp)])
3. 🔄 Implement hard constraints (C1-C17) using model.Add()
4. 🔄 Implement soft constraint scoring (S1-S16)
5. ✅ Validate solution extraction and output JSON

**When ready:** Proceed to constraint implementation following `docs/constraints_master.md` and code patterns in existing C*.py files.

