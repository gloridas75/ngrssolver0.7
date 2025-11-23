# Working Hours Calculation System

## Canonical Working-Hours Model

This document defines the canonical (authoritative) model for all working-hours calculations across the NGRS Solver system.

### Core Formula

For any single shift with start → end times:

```
gross_hours = duration in hours (start to end, may span midnight)

lunch_hours = 1.0 if gross_hours > 6.0 else 0.0
              (1-hour meal break applies only if shift exceeds 6 hours)

normal_hours = min(gross_hours, 9.0) - lunch_hours
               (working hours capped at 9h per shift, minus meal break)

ot_hours = max(0.0, gross_hours - 9.0)
           (overtime = everything beyond 9h per shift)

paid_hours = gross_hours
             (employee gets paid for full duration including lunch)
```

### Examples

| Shift | Gross | Lunch | Normal | OT | Notes |
|-------|-------|-------|--------|-----|-------|
| 09:00-18:00 | 9.0 | 1.0 | 8.0 | 0.0 | Standard 9h day shift, 1h lunch |
| 09:00-20:00 | 11.0 | 1.0 | 8.0 | 2.0 | 11h shift = 8h normal + 1h lunch + 2h OT |
| 19:00-07:00 | 12.0 | 1.0 | 8.0 | 3.0 | 12h overnight shift = 8h normal + 1h lunch + 3h OT |
| 14:00-17:00 | 3.0 | 0.0 | 3.0 | 0.0 | Short 3h shift, no lunch (≤6h) |
| 14:00-21:00 | 7.0 | 1.0 | 6.0 | 0.0 | 7h shift = 6h normal + 1h lunch (still under 9h cap) |

### Key Insights

1. **Lunch Rule**: Only applies when `gross > 6.0` hours
   - Why: Industry standard—short shifts don't include meal breaks
   - Not cumulative: One lunch per shift, max, regardless of duration

2. **Normal Hours Cap**: Capped at 9h per shift
   - Why: Regulatory limit on daily working hours before OT
   - Formula: `min(gross, 9.0) - lunch` ensures normal never exceeds 8h with lunch

3. **OT Hours**: Anything beyond 9h gross
   - Why: Separate regulatory tracking and cost management
   - Formula: `max(0, gross - 9.0)` is simple and clear

4. **Paid Hours**: Always equals gross
   - Why: Employee compensation includes meal break time
   - Exception handling: Some jurisdictions may differ (future enhancement)

---

## Usage by Constraint

### C1: Daily Gross Hours Cap (by Scheme)

**Constraint**: `∑(gross_hours on same day) ≤ scheme_limit`

- Scheme A: ≤ 14h per day
- Scheme B: ≤ 13h per day
- Scheme P: ≤ 9h per day

**Use**: `span_hours()` → sum gross for each day per employee

**Logic**:
```python
daily_gross_by_emp = defaultdict(float)
for assignment in assignments_same_day:
    gross = span_hours(assignment.start_dt, assignment.end_dt)
    daily_gross_by_emp[emp_id] += gross

# Validate
for emp_id, scheme in employees_by_id.items():
    max_gross = max_hours_by_scheme[scheme]
    assert daily_gross_by_emp[emp_id] <= max_gross
```

---

### C2: Weekly Normal Hours Cap

**Constraint**: `∑(normal_hours per week) ≤ 44h`

**Use**: `split_shift_hours()` → extract `normal` field → sum weekly

**Why normal (not gross)?** Because:
- Lunch hours are unpaid work time (meal break)
- OT hours are tracked separately with different regulations
- 44h is the regulatory ceiling on *working time*, not including meal breaks

**Logic**:
```python
weekly_normal_by_emp = defaultdict(float)
for assignment in assignments_same_week:
    hours_dict = split_shift_hours(assignment.start_dt, assignment.end_dt)
    weekly_normal_by_emp[emp_id] += hours_dict['normal']

# Validate
for emp_id in employees:
    assert weekly_normal_by_emp[emp_id] <= 44.0
```

---

### C17: Monthly OT Cap

**Constraint**: `∑(ot_hours per month) ≤ 72h`

**Use**: `split_shift_hours()` → extract `ot` field → sum monthly

**Why OT (not total)?** Because:
- OT is tracked separately for cost and fatigue management
- OT is anything beyond the 9h per-shift regulatory limit
- Monthly OT limit is a separate compliance requirement

**Logic**:
```python
monthly_ot_by_emp = defaultdict(float)
for assignment in assignments_same_month:
    hours_dict = split_shift_hours(assignment.start_dt, assignment.end_dt)
    monthly_ot_by_emp[emp_id] += hours_dict['ot']

# Validate
for emp_id in employees:
    assert monthly_ot_by_emp[emp_id] <= 72.0
```

---

## Implementation: `time_utils.py`

### Functions

#### `span_hours(start_dt, end_dt) → float`
- **Purpose**: Calculate total gross hours between two datetimes
- **Handles**: Overnight shifts (end before start → assumes next day)
- **Returns**: Gross hours as float
- **Example**: `span_hours(09:00, 18:00)` → `9.0`

#### `lunch_hours(gross) → float`
- **Purpose**: Calculate meal break duration
- **Logic**: `1.0 if gross > 6.0 else 0.0`
- **Returns**: Hours (0.0 or 1.0)
- **Example**: `lunch_hours(6.5)` → `1.0`

#### `split_normal_ot(gross) → tuple[float, float]`
- **Purpose**: Split working hours into normal and OT components
- **Returns**: `(normal_hours, ot_hours)`
- **Example**: `split_normal_ot(11.0)` → `(8.0, 2.0)`

#### `split_shift_hours(start_dt, end_dt) → dict`
- **Purpose**: Complete breakdown of a shift
- **Returns**: Dictionary with keys:
  - `gross`: Total duration
  - `lunch`: Meal break hours
  - `normal`: Working hours for 44h cap
  - `ot`: Overtime hours
  - `paid`: Paid hours (usually = gross)
- **Example**: 
  ```python
  split_shift_hours(09:00, 20:00)
  # {
  #     'gross': 11.0,
  #     'lunch': 1.0,
  #     'normal': 8.0,
  #     'ot': 2.0,
  #     'paid': 11.0
  # }
  ```

#### `calculate_weekly_normal_hours(shifts) → float`
- **Purpose**: Sum normal hours for a week
- **Use Case**: Checking 44h weekly cap
- **Input**: List of `(start_dt, end_dt)` tuples
- **Returns**: Total normal hours
- **Example**: `calculate_weekly_normal_hours([...])` → `44.0`

#### `calculate_monthly_ot_hours(shifts) → float`
- **Purpose**: Sum OT hours for a month
- **Use Case**: Checking 72h monthly OT cap
- **Input**: List of `(start_dt, end_dt)` tuples
- **Returns**: Total OT hours
- **Example**: `calculate_monthly_ot_hours([...])` → `68.5`

#### `calculate_daily_gross_hours(shifts_same_day) → float`
- **Purpose**: Sum gross hours for a single day
- **Use Case**: Checking daily gross cap (14h/13h/9h by scheme)
- **Input**: List of `(start_dt, end_dt)` tuples for same day
- **Returns**: Total gross hours
- **Example**: `calculate_daily_gross_hours([...])` → `13.5`

---

## Integration into Constraints

### C1: Daily Gross Hours (by Scheme)

**File**: `context/constraints/C1_mom_daily_hours.py`

```python
from context.engine.time_utils import split_shift_hours

# For each employee on each day
daily_gross = 0
for assignment in same_day_assignments:
    hours_dict = split_shift_hours(assignment.start, assignment.end)
    daily_gross += hours_dict['gross']

# Validate against scheme
scheme_limit = {'A': 14, 'B': 13, 'P': 9}[employee.scheme]
assert daily_gross <= scheme_limit
```

### C2: Weekly Normal Hours + Monthly OT

**File**: `context/constraints/C2_mom_weekly_hours.py`

```python
from context.engine.time_utils import split_shift_hours

# Weekly normal
weekly_normal = 0
for assignment in same_week_assignments:
    hours_dict = split_shift_hours(assignment.start, assignment.end)
    weekly_normal += hours_dict['normal']
assert weekly_normal <= 44.0

# Monthly OT
monthly_ot = 0
for assignment in same_month_assignments:
    hours_dict = split_shift_hours(assignment.start, assignment.end)
    monthly_ot += hours_dict['ot']
assert monthly_ot <= 72.0
```

### C17: Monthly OT Cap

**File**: `context/constraints/C17_ot_monthly_cap.py`

```python
from context.engine.time_utils import split_shift_hours, calculate_monthly_ot_hours

# Sum OT for the month
shifts = [(a.start, a.end) for a in same_month_assignments]
monthly_ot = calculate_monthly_ot_hours(shifts)
assert monthly_ot <= 72.0
```

---

## Testing

Run the test suite:

```bash
PYTHONPATH=. python context/engine/test_time_utils.py
```

**Output**:
```
============================================================
Testing time_utils.py - Working Hours Calculation
============================================================

✓ span_hours tests passed
✓ lunch_hours tests passed
✓ split_normal_ot tests passed
✓ split_shift_hours tests passed
✓ weekly and monthly totals tests passed
✓ daily gross hours tests passed

============================================================
✅ All tests passed!
============================================================
```

---

## Design Rationale

### Why Separate `normal`, `lunch`, and `ot`?

1. **Regulatory Separation**: Different regulations apply to each
   - Normal: 44h weekly cap (working time directive)
   - Lunch: Typically unpaid (labor code varies by jurisdiction)
   - OT: 72h monthly cap (fatigue management)

2. **Cost Management**: Each has different compensation
   - Normal: Base hourly rate
   - Lunch: Often unpaid or special rate
   - OT: Premium rate (typically 1.5x or 2x)

3. **Compliance Tracking**: Auditing requires separate tracking
   - Regulators need separate line items
   - Financial systems reconcile by type
   - Fatigue management focused on OT only

### Why `lunch_hours > 6.0`?

- **Industry Standard**: Most labor codes use 6-hour threshold
- **Practical**: Shifts under 6h rare in modern scheduling
- **Clear**: No ambiguity—either meal break applies or doesn't
- **Conservative**: Favors employee by including lunch time

### Why Cap Normal at 9h?

- **Regulatory**: Legal maximum working time per shift (varies by jurisdiction, commonly 8-10h)
- **Health & Safety**: Fatigue limits per single shift
- **Standard**: Industry practice separates 9h shift + OT beyond that
- **Our Model**: Aligns with "normal" capped at 9h, OT beyond

---

## Future Enhancements

### Jurisdiction-Specific Rules

Currently hardcoded; future updates could parameterize:
- Lunch break threshold (currently `> 6.0`)
- Daily working hour cap (currently 9.0)
- Weekly normal hours cap (currently 44.0)
- Monthly OT cap (currently 72.0)
- Lunch break duration (currently 1.0h)

### Meal Break Compensation

Currently assumes unpaid. Future enhancement:
- `paid_if_compensated`: If jurisdiction requires paid lunch
- `meal_break_rate`: If special rate applies

### Split Shifts

Currently assumes contiguous shifts. Future enhancement:
- Multiple shifts per day with rest periods
- Break-time inclusion/exclusion

### Regional Variations

Future: Load rules from config or jurisdiction parameter
```python
time_utils.configure(
    jurisdiction='SG',  # Singapore
    lunch_threshold=6.0,
    normal_cap=9.0,
    weekly_cap=44.0,
    monthly_ot_cap=72.0
)
```

---

## References

- **Labor Code (Singapore)**: Section 36, 40 (working hours, overtime)
- **Labor Code (Malaysia)**: Similar 44h weekly standard
- **Industry Standards**: Police/Security sector scheduling practices
- **Internal**: See `PHASE1_README.md` for Phase 1 architecture overview

---

## Checklist: Using This System

- [ ] Import `split_shift_hours` when calculating hours
- [ ] Use `.get('normal')` for 44h weekly cap
- [ ] Use `.get('ot')` for 72h monthly cap
- [ ] Use `.get('gross')` for daily scheme limits
- [ ] Use helper functions (`calculate_weekly_normal_hours`, etc.) for aggregation
- [ ] Add test cases if modifying this module
- [ ] Update documentation if changing formulas
- [ ] Run `test_time_utils.py` after any changes

---

*Last Updated: 2025-11-11*  
*Version: 1.0 - Canonical Working-Hours Model*
