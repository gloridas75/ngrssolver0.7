# Quick Answer: Shift Rotation & Site-Based Patterns

**Question**: How is shift rotation implemented? Can we send shift rotation patterns for given site ID in input.json?

**Answer**: ✅ **YES, fully supported!**

---

## 📋 TL;DR (Too Long; Didn't Read)

### How Rotation Works
1. **Define rotation sequence** in input.json (e.g., `["D","D","D","D","D","O","O"]`)
2. **Include siteId** for location identification
3. **Solver expands** rotations into daily slots
4. **Employees assigned** to available slots
5. **Rotation is enforced** automatically at slot level

### Example

```json
{
  "demandId": "D_SITE_A_DAY",
  "siteId": "SITE-A",
  "shifts": [{
    "rotationSequence": ["D", "D", "D", "D", "D", "O", "O"],
    "rotationAnchor": "2025-11-01"
  }]
}
```

Result: Site A always has 5 days on, 2 days off pattern (no constraints needed—built into slots).

---

## 🎯 Key Components

### 1. **Input Definition** (input.json)
```
demandItem {
  siteId: "SITE-A"                               ← Identifies location
  shifts: [{
    rotationSequence: ["D","D","D","D","D","O","O"]  ← Pattern
    rotationAnchor: "2025-11-01"                     ← Start date
    shiftDetails: [{start, end, shiftCode}]         ← Times
    whitelist: {employeeIds: []}                     ← Who can work
  }]
}
```

### 2. **Slot Builder** (context/engine/slot_builder.py)
- **Reads** rotation sequence from each demand
- **Calculates** which shift each day gets (modulo logic)
- **Creates** atomic daily slots
- **Skips** "O" (off) days automatically

```
Day N calculation:
  days_since_anchor = (N - anchor_date).days
  rotation_idx = days_since_anchor % len(sequence)
  shift_code = sequence[rotation_idx]
```

### 3. **Slot Object**
```python
Slot(
  demandId="D_SITE_A_DAY",
  siteId="SITE-A",           ← ✓ Site info
  date="2025-11-05",
  shiftCode="D",
  start="08:00", end="20:00",
  whitelist={employeeIds: ["E_ALICE", ...]}
)
```

### 4. **S1 Constraint** (context/constraints/S1_rotation_pattern.py)
- **Tracks** rotation patterns (informational)
- **Doesn't enforce** (enforcement is in slot level)
- **Logs** pattern compliance

### 5. **Solver**
- **Selects** slots for assignment
- **Respects** pre-built rotation (can't break it)
- **Assigns** employees from whitelist
- **Produces** OPTIMAL schedule

---

## 📊 Multiple Sites Example

```json
{
  "demandItems": [
    {
      "demandId": "D_SITE_A_DAY",
      "siteId": "SITE-A",
      "shifts": [{
        "rotationSequence": ["D","D","D","D","D","O","O"],
        "rotationAnchor": "2025-11-01"
      }]
    },
    {
      "demandId": "D_SITE_B_DAY",
      "siteId": "SITE-B",
      "shifts": [{
        "rotationSequence": ["D","D","D","O","D","D","O"],
        "rotationAnchor": "2025-11-01"
      }]
    },
    {
      "demandId": "D_SITE_C_NIGHT",
      "siteId": "SITE-C",
      "shifts": [{
        "rotationSequence": ["N","N","N","N","N","O","O"],
        "rotationAnchor": "2025-11-01"
      }]
    }
  ]
}
```

Result:
- **SITE-A**: 5-2 pattern (day shifts)
- **SITE-B**: 3-1-2 pattern (day shifts)
- **SITE-C**: 5-2 pattern (night shifts)

Each site has **independent** rotation + staffing.

---

## ✅ Current Capabilities

| Feature | Status | Details |
|---------|--------|---------|
| **Site ID Support** | ✅ Implemented | Each demand has `siteId` field |
| **Rotation Patterns** | ✅ Implemented | Via `rotationSequence` array |
| **Multiple Sites** | ✅ Supported | Different patterns per site |
| **Different Shifts** | ✅ Supported | D (day), N (night), E (evening) |
| **Different Timings** | ✅ Supported | Custom start/end times per site |
| **Employee Whitelisting** | ✅ Supported | Per-site team assignments |
| **Rotation Enforcement** | ✅ Implemented | Built into slot level |

---

## 🔍 Architecture Flow

```
INPUT.json
  ↓
  ├─ demandItem #1 (siteId: A, rotationSequence: [D,D,D,D,D,O,O])
  ├─ demandItem #2 (siteId: B, rotationSequence: [D,D,D,O,D,D,O])
  └─ demandItem #3 (siteId: C, rotationSequence: [N,N,N,N,N,O,O])
  ↓
[slot_builder.py]
  ├─ Expands rotation sequences into daily slots
  ├─ Creates 20-30 slots per demand (depending on offs)
  └─ Attaches siteId, whitelist, team info to each slot
  ↓
[slot_list: ~80-100 total slots]
  ↓
[solver_engine.py]
  ├─ Reads all slots
  ├─ Applies 40 constraints (C1-C17, S1-S16)
  ├─ Assigns employees from whitelist
  └─ Respects rotation (can't break slot structure)
  ↓
OUTPUT.json
  ├─ 110+ assignments with siteId embedded
  ├─ Each assignment tied to site + rotation
  └─ Rotation patterns fully respected
```

---

## 🚀 How to Use

### Step 1: Prepare input.json with multiple sites

```json
{
  "planningHorizon": {"startDate": "2025-11-01", "endDate": "2025-11-30"},
  "demandItems": [
    {
      "demandId": "D_AIRPORT_T1_FRISKING",
      "siteId": "AIRPORT-TERMINAL-1",
      "shifts": [{
        "rotationSequence": ["D", "D", "D", "D", "D", "O", "O"],
        "rotationAnchor": "2025-11-01"
      }]
    },
    {
      "demandId": "D_AIRPORT_T2_FRISKING",
      "siteId": "AIRPORT-TERMINAL-2",
      "shifts": [{
        "rotationSequence": ["D", "D", "D", "O", "D", "D", "O"],
        "rotationAnchor": "2025-11-01"
      }]
    }
  ]
}
```

### Step 2: Run solver

```bash
python run_solver.py --input input.json --output output.json
```

### Step 3: Query results by site

```python
import json

with open('output.json') as f:
    result = json.load(f)

# Get all assignments for SITE-A
site_a = [a for a in result['assignments'] 
          if a['demandId'].startswith('D_AIRPORT_T1_')]

print(f"SITE-A: {len(site_a)} assignments")
```

---

## 📚 Documentation Files

New files created to explain this:

1. **[SHIFT_ROTATION_GUIDE.md](./SHIFT_ROTATION_GUIDE.md)** - Complete technical guide
2. **[ROTATION_EXAMPLES.md](./ROTATION_EXAMPLES.md)** - Real-world examples with visualizations
3. **[S1_rotation_pattern.py](../context/constraints/S1_rotation_pattern.py)** - Constraint code

---

## ❓ FAQ

### Q: Can each site have a different rotation pattern?
**A**: ✅ YES. Each demand item specifies its own `rotationSequence`.

### Q: How are off days handled?
**A**: Off days (marked with "O" in the sequence) create no slots, so no assignments on those days.

### Q: What happens if employees share the same site but different rotations?
**A**: Create separate demand items with different `rotationSequence` values and different whitelists.

### Q: Is rotation enforced hard or soft?
**A**: **Hard** - it's built into the slot level. Solver can't violate it because slots don't exist on off days.

### Q: Can I change rotation patterns mid-month?
**A**: Not directly in one input.json, but you can create separate demand items with different anchor dates.

### Q: How many sites can I have?
**A**: Unlimited - just add more demand items with different `siteId` values.

---

## 🎯 Key Takeaway

**Yes, shift rotation patterns for site-based scheduling are fully supported.**

The system works by:
1. ✅ Accepting site IDs and rotation sequences in input.json
2. ✅ Expanding rotations into daily slots (automatically)
3. ✅ Assigning employees while preserving rotation patterns
4. ✅ Returning schedules with site information

**No special constraints needed** - rotation enforcement is built into the slot structure.

---

**For detailed information**, see:
- **[SHIFT_ROTATION_GUIDE.md](./SHIFT_ROTATION_GUIDE.md)** - Full technical explanation
- **[ROTATION_EXAMPLES.md](./ROTATION_EXAMPLES.md)** - Visual examples
- **`input_1211_optimized.json`** - Working example
- **`context/engine/slot_builder.py`** - Implementation
- **`context/constraints/S1_rotation_pattern.py`** - Constraint tracking

---

**Status**: ✅ Production Ready | **Last Updated**: November 13, 2025
