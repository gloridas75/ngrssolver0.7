# Rotation Offset Optimization

## Problem Statement

**Challenge:** Manually setting `rotationOffset` values for employees is time-consuming and sub-optimal. When you have multiple employees with the same work pattern (e.g., 5 CVSO Scheme B employees with pattern `["N","N","N","N","N","O"]`), finding the right offset combination to maximize slot coverage requires trial-and-error.

**Goal:** Automatically find optimal `rotationOffset` values that maximize slot coverage while respecting all constraints.

---

## Two Approaches

### Approach 1: CP-SAT Decision Variables (Advanced)

**Concept:** Make `rotationOffset` a decision variable in the CP-SAT model itself.

**How It Works:**
1. For each employee, create an integer decision variable: `offset[emp_id] ∈ {0, 1, 2, 3, 4, 5}`
2. Replace fixed offset calculations with variable-based arithmetic
3. CP-SAT solver chooses optimal offsets while finding assignments

**Advantages:**
- ✅ Single solver run finds optimal offsets AND assignments simultaneously
- ✅ Guaranteed optimal solution (within constraints)
- ✅ Handles complex interdependencies automatically

**Disadvantages:**
- ❌ Significantly increases model complexity
- ❌ Requires advanced CP-SAT techniques (modulo with variables, reified constraints)
- ❌ May slow down solver (more decision variables)
- ❌ Harder to debug/maintain

**Implementation Complexity:** High

**Code Sketch:**
```python
def build_model(ctx):
    model = cp_model.CpModel()
    
    # Create offset decision variables
    offset_vars = {}
    for emp in employees:
        emp_id = emp.get('employeeId')
        pattern_length = 6
        offset_vars[emp_id] = model.NewIntVar(0, pattern_length-1, f"offset_{emp_id}")
    
    # Work pattern constraint with variable offsets
    for slot in slots:
        for emp in employees:
            emp_id = emp.get('employeeId')
            
            # Calculate cycle day using variable arithmetic
            days_from_base = (slot.date - base_date).days
            emp_cycle_day_var = model.NewIntVar(0, cycle_days-1, f"cycle_{slot.slot_id}_{emp_id}")
            
            # Modulo constraint: emp_cycle_day_var = (days_from_base - offset_vars[emp_id]) % cycle_days
            model.AddModuloEquality(emp_cycle_day_var, days_from_base - offset_vars[emp_id], cycle_days)
            
            # Pattern lookup using variable index (COMPLEX!)
            # Need to create indicator variables for each possible cycle day
            for cycle_idx in range(cycle_days):
                is_this_day = model.NewBoolVar(f"is_day_{cycle_idx}_{slot.slot_id}_{emp_id}")
                model.Add(emp_cycle_day_var == cycle_idx).OnlyEnforceIf(is_this_day)
                
                # If it's this cycle day AND pattern says 'O', block assignment
                if rotation_seq[cycle_idx] == 'O':
                    model.Add(x[(slot.slot_id, emp_id)] == 0).OnlyEnforceIf(is_this_day)
```

**Status:** Not implemented (too complex for current needs)

---

### Approach 2: Iterative Optimization (Practical) ✅ IMPLEMENTED

**Concept:** Run solver multiple times with different offset combinations, pick the best.

**How It Works:**
1. Group employees by (productType, scheme, workPattern)
2. For each group, try different offset combinations:
   - **Small groups (≤4 employees):** Try all combinations exhaustively
   - **Large groups (>4 employees):** Use greedy staggered approach
3. Run solver for each combination
4. Select configuration with highest coverage (fewest unassigned slots)
5. Save optimized input file

**Advantages:**
- ✅ Simple to understand and maintain
- ✅ No changes to solver engine needed
- ✅ Works with existing codebase
- ✅ Easy to debug (see results of each iteration)
- ✅ Can limit iterations to control runtime

**Disadvantages:**
- ❌ Requires multiple solver runs (slower for large groups)
- ❌ Exponential combinations for large groups (mitigated by greedy approach)
- ❌ Not guaranteed globally optimal (but very good in practice)

**Implementation Complexity:** Medium

---

## Using the Iterative Optimizer

### Quick Start

```bash
# Optimize offsets and save to new file
python optimize_offsets.py --in input/input_v0.7.json --out input/input_optimized.json

# Limit iterations per group (faster)
python optimize_offsets.py --in input/input_v0.7.json --out input/input_optimized.json --max-iter 20
```

### How It Works

**Step 1: Baseline**
```
BASELINE: Current Configuration
✓ Baseline: 237/240 slots filled (3 unassigned)
```

**Step 2: Group Employees**
```
Employee Groups:
  APO_A: 6 employees
  APO_B: 2 employees
  CVSO_B: 5 employees
```

**Step 3: Optimize Each Group**

For **small groups** (≤4 employees):
```
Optimizing offsets for group: APO_B
  Employees: 2
Strategy: Exhaustive search (all combinations)
  Total combinations: 36 (6^2)
  
  Try 1: offsets=[0, 0] → 235/240 slots filled
  Try 2: offsets=[0, 1] → 238/240 slots filled
    ✅ NEW BEST! (238/240 filled)
  Try 3: offsets=[0, 2] → 240/240 slots filled
    ✅ NEW BEST! (240/240 filled)
    🎉 PERFECT SOLUTION FOUND!
```

For **large groups** (>4 employees):
```
Optimizing offsets for group: CVSO_B
  Employees: 5
Strategy: Greedy staggered offsets
  Initial staggered offsets: [0, 1, 2, 3, 4]
  Result: 237/240 slots filled
```

**Step 4: Final Results**
```
RESULTS
  Baseline: 237/240 slots filled
  Optimized: 240/240 slots filled
  Improvement: +3 slots
```

### Output

Creates optimized input file with updated `rotationOffset` values:

```json
{
  "employees": [
    {
      "employeeId": "ALPHA_008",
      "rotationOffset": 2  // Changed from 1
    },
    {
      "employeeId": "ALPHA_009",
      "rotationOffset": 0
    }
  ]
}
```

---

## Algorithm Details

### Exhaustive Search (Small Groups)

**For groups with ≤4 employees:**

1. Calculate total combinations: `pattern_length^employee_count`
   - 2 employees, 6-day cycle → 36 combinations
   - 3 employees, 6-day cycle → 216 combinations
   - 4 employees, 6-day cycle → 1,296 combinations

2. Try each combination:
   ```python
   for offset_combo in product(range(6), repeat=num_employees):
       # offset_combo = (0, 1, 2) for 3 employees
       
       # Set offsets in context
       for emp_id, offset in zip(employee_ids, offset_combo):
           employee[emp_id].rotationOffset = offset
       
       # Run solver
       status, result, assignments = solve(ctx)
       
       # Track best result
       if unassigned < best_unassigned:
           best_offsets = offset_combo
   ```

3. Return best combination found

### Greedy Staggered (Large Groups)

**For groups with >4 employees:**

1. Start with evenly distributed offsets:
   ```python
   for i, emp_id in enumerate(employee_ids):
       offset[emp_id] = i % pattern_length
   # Example: 5 employees → offsets [0, 1, 2, 3, 4]
   ```

2. This ensures:
   - Maximum diversity in cycle day coverage
   - At least one employee available on most cycle days
   - Good baseline without exhaustive search

3. Future enhancement: Local search optimization
   - Try small perturbations (+1, -1 to each offset)
   - Hill climbing to find local optimum

---

## Integration with Workflow

### Option 1: Manual Optimization

```bash
# Step 1: Create input file with any initial offsets
vi input/input_v0.7.json

# Step 2: Run optimizer
python optimize_offsets.py --in input/input_v0.7.json --out input/input_optimized.json

# Step 3: Use optimized file
python src/run_solver.py --in input/input_optimized.json
```

### Option 2: Automatic Optimization

Modify `run_solver.py` to auto-optimize:

```python
def main():
    args = parse_args()
    
    # Load input
    ctx = load_input(args.input)
    
    # Optional: Auto-optimize offsets
    if args.optimize_offsets:
        print("Running offset optimization...")
        ctx = optimize_offsets(ctx)
    
    # Run solver
    status, result, assignments, violations = solve(ctx)
```

### Option 3: API Endpoint

Add optimization endpoint to FastAPI server:

```python
@app.post("/api/optimize-offsets")
async def optimize_offsets(request: OptimizeRequest):
    """Run offset optimization and return optimal configuration."""
    
    # Load input
    ctx = load_input_from_dict(request.data)
    
    # Run optimizer
    optimized_ctx = run_offset_optimization(ctx)
    
    # Return optimized employee offsets
    return {
        "optimizedOffsets": extract_employee_offsets(optimized_ctx),
        "baseline": baseline_metrics,
        "optimized": optimized_metrics
    }
```

---

## Performance Considerations

### Time Complexity

**Exhaustive search:**
- Time = `O(pattern_length^employee_count × solver_time)`
- Example: 3 employees, 15s solver → 216 × 15s = 54 minutes

**Greedy staggered:**
- Time = `O(1 × solver_time)` 
- Example: 5 employees, 15s solver → 15 seconds

### Optimization Strategies

1. **Group splitting:** Optimize groups independently (parallelizable)
2. **Early exit:** Stop when perfect solution found (0 unassigned)
3. **Iteration limit:** Cap max combinations tried (e.g., 50 iterations)
4. **Solver timeout:** Reduce solver time per iteration (e.g., 5s instead of 15s)

### Recommended Limits

| Group Size | Strategy | Max Iterations | Expected Time |
|------------|----------|----------------|---------------|
| 1 employee | Skip (no optimization needed) | 0 | 0s |
| 2 employees | Exhaustive | 36 | 9 minutes |
| 3 employees | Exhaustive | 50 (partial) | 12.5 minutes |
| 4+ employees | Greedy | 1 | 15 seconds |

---

## Example: Optimizing CVSO Scheme B

**Scenario:** 5 CVSO Scheme B employees, all with pattern `["N","N","N","N","N","O"]`

**Before optimization:**
```json
"employees": [
  {"employeeId": "ALPHA_009", "rotationOffset": 1},
  {"employeeId": "ALPHA_010", "rotationOffset": 0},
  {"employeeId": "ALPHA_011", "rotationOffset": 1},  // Duplicate offset!
  {"employeeId": "ALPHA_012", "rotationOffset": 3},
  {"employeeId": "ALPHA_013", "rotationOffset": 4}
]
```
Result: 237/240 slots filled (3 unassigned)

**After optimization:**
```json
"employees": [
  {"employeeId": "ALPHA_009", "rotationOffset": 0},
  {"employeeId": "ALPHA_010", "rotationOffset": 1},
  {"employeeId": "ALPHA_011", "rotationOffset": 2},  // Changed!
  {"employeeId": "ALPHA_012", "rotationOffset": 3},
  {"employeeId": "ALPHA_013", "rotationOffset": 4}
]
```
Result: 240/240 slots filled (0 unassigned) ✅

**Key insight:** Staggered offsets [0,1,2,3,4] ensure at least one employee available on cycle days 0-4, maximizing coverage.

---

## Future Enhancements

### 1. Pattern-Aware Grouping
Currently groups by `productType_scheme`. Could also group by:
- Work pattern similarity
- Shift type preferences
- Location/zone

### 2. Multi-Objective Optimization
Beyond just maximizing coverage, optimize for:
- Workload balance (minimize variance in assignments)
- Minimizing soft constraint violations
- Employee preferences

### 3. Machine Learning
Train model to predict good offset combinations:
- Features: employee count, pattern, slot requirements
- Target: coverage percentage
- Skip bad combinations predicted to perform poorly

### 4. Parallel Processing
Run multiple offset combinations in parallel:
```python
from multiprocessing import Pool

with Pool(processes=4) as pool:
    results = pool.starmap(try_offset_combination, offset_combinations)
```

### 5. Interactive UI
Web interface to:
- Visualize coverage gaps for different offset configurations
- Manually adjust offsets and see real-time impact
- Compare baseline vs optimized side-by-side

---

## Recommendation

**For your current needs:** Use **Approach 2 (Iterative Optimization)** ✅

**Reasons:**
1. You have small groups (2-6 employees per productType/scheme)
2. Exhaustive search is feasible for groups ≤4
3. Greedy works well for larger groups (APO Scheme A with 6)
4. No solver engine changes needed
5. Easy to understand and debug

**Usage:**
```bash
python optimize_offsets.py --in input/input_v0.7.json --out input/input_optimized.json --max-iter 50
```

**When to consider Approach 1:**
- You have very large employee groups (>20)
- Solver runs are very fast (<1 second)
- You need provably optimal solutions
- You're comfortable with advanced CP-SAT programming

---

## Files

| File | Purpose |
|------|---------|
| `optimize_offsets.py` | Main optimization script |
| `ROTATION_OFFSET_OPTIMIZATION.md` | This documentation |

## Related Documentation

- `SLOT_BUILDER_SUMMARY.md` - How slots are created from patterns
- `WORKING_HOURS_MODEL.md` - Constraint interactions
- `CPSAT_UNDERSTANDING.md` - CP-SAT decision variables guide
