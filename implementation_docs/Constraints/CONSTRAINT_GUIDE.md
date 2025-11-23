# How to Build New Constraints

Quick guide for adding constraints to the NGRS solver.

## Constraint Types

### Hard Constraints (C1-C17)
- Block infeasible solutions
- Added in `context/constraints/C*.py`
- Must use `model.Add()` from CP-SAT
- Violations counted as hard failures

### Soft Constraints (S1-S16)
- Guide solver toward better solutions
- Don't block feasibility
- Use objective coefficients or penalties
- Violations counted as soft penalties

## Adding a Constraint

### 1. Edit the constraint file
Location: `context/constraints/C[N]_[name].py`

```python
def add_constraints(model, ctx):
    """Description of what constraint does."""
    
    employees = ctx.get('employees', [])
    slots = ctx.get('slots', [])
    x = ctx.get('x', {})  # Decision variables
    
    # Extract requirements
    min_value = 10  # Example
    
    print(f"[C#] Constraint Name")
    print(f"     Total items: {len(employees)}")
    
    constraints_added = 0
    
    # Add constraints
    for slot in slots:
        for emp in employees:
            if some_condition:
                model.Add(x[(slot.slot_id, emp_id)] <= some_limit)
                constraints_added += 1
    
    print(f"     Added {constraints_added} constraints\n")
```

### 2. Available Context Objects

```python
ctx = {
    'employees': [...],           # Employee data
    'slots': [...],               # Slot objects with start/end/date
    'x': {(slot_id, emp_id): var},  # Decision variables
    'demandItems': [...],         # Original demand specs
    'planningHorizon': {...},     # Start/end dates
    'constraintList': [...],      # Constraint configs
}
```

### 3. Decision Variables

```python
x[(slot.slot_id, employee_id)]  # BoolVar: 1 if assigned, 0 otherwise

# Only exists if employee is whitelisted for slot
# Check before using: if (slot_id, emp_id) in x
```

### 4. Common Patterns

#### Prevent Conflicting Assignments
```python
# Cannot assign both slot1 and slot2 to same employee
model.Add(x[(slot1_id, emp_id)] + x[(slot2_id, emp_id)] <= 1)
```

#### Require Assignment if Condition
```python
# If condition true, must assign to at least one slot
if some_condition:
    slots_for_demand = [s for s in slots if s.demandId == target]
    model.Add(sum(x.get((s.slot_id, emp_id), 0) for s in slots_for_demand) >= 1)
```

#### Limit Assignments per Employee
```python
# Employee can work at most N shifts
model.Add(sum(x.get((s.slot_id, emp_id), 0) for s in slots) <= N)
```

### 5. Post-Solve Validation (Optional)

Add validation logic in `context/engine/solver_engine.py` `calculate_scores()` function:

```python
# Find the CHECK section (e.g., "# ========== C5 CHECK: ...")
# Add your validation:

for assignment in assignments:
    emp_id = assignment.get('employeeId')
    # ... check condition ...
    if violation_detected:
        score_book.hard("C#", "Violation message")
```

## Testing Your Constraint

```bash
# Run solver with test input
python src/run_solver.py --in input/input_1211_optimized.json --time 15

# Check output for your constraint
grep "\[C#\]" /tmp/solver.log

# Verify violations in output
python -c "
import json
with open('output/output_*.json') as f:
    data = json.load(f)
    violations = data['scoreBreakdown']['hard']['violations']
    for v in violations:
        if v['id'] == 'C#':
            print(v)
"
```

## Constraint Loading

Constraints are loaded automatically in order:
1. `C1-C17.py` files (hard constraints)
2. `S1-S16.py` files (soft constraints)

Loaded in `context/engine/solver_engine.py` `apply_constraints()` function.

## Tips

- ✅ Use `x.get((slot_id, emp_id))` to safely check variable existence
- ✅ Print debug info at start of constraint function
- ✅ Count constraints added and report
- ✅ Test with small input first
- ❌ Don't modify solver_engine.py core logic
- ❌ Don't use floating point in constraints (use integers)
- ❌ Don't forget to handle missing context data

## Current Status

**Implemented Constraints**:
- ✅ C4 (Rest Period)
- ✅ C12 (Team Completeness)
- ✅ C16 (No Overlap)

**Next Priority**:
- S1-S5 (Soft constraints)
- C13-C14 (Optional)

