# Shift Rotation Pattern Implementation Guide

**Date**: November 13, 2025  
**Project**: NGRS Solver v0.7  
**Topic**: Understanding Shift Rotation Constraints

---

## 🎯 Overview

The shift rotation pattern system in NGRS Solver allows you to define **repeating shift schedules** for specific sites and demands. This ensures that employees follow predictable rotation cycles (like 5 days on, 2 days off) while maintaining fairness and coverage.

---

## 📋 How Shift Rotation Works

### 1. **Rotation Sequence Definition**

Each shift in the input.json defines a rotation pattern as an array:

```json
"rotationSequence": ["D", "D", "D", "D", "D", "O", "O"]
```

This means:
- **Day 1-5**: "D" shift (work)
- **Day 6-7**: "O" shift (off/day off)
- **Pattern repeats** every 7 days (rotationCycleDays: 7)

### 2. **Key Rotation Parameters**

```json
{
  "demandId": "D_DAY_FRISKING",
  "siteId": "SITE-A",                          // Site location
  "shifts": [{
    "shiftDetails": [
      {
        "shiftCode": "D",                       // Shift code (D, N, etc.)
        "start": "08:00",                       // Start time
        "end": "20:00",                         // End time
        "nextDay": false
      }
    ],
    "rotationSequence": ["D", "D", "D", "D", "D", "O", "O"],   // Pattern
    "rotationCycleDays": 7,                     // Cycle length (default: length of sequence)
    "rotationAnchor": "2025-11-01",            // Start date for rotation
    "coverage": "FREQ=DAILY;INTERVAL=1",        // Daily coverage
    "preferredTeams": ["TEAM-1"],               // Team assignment
    "whitelist": {
      "employeeIds": ["E_ALICE_FRISKER", "E_BOB_FRISKER", ...]  // Who can work
    }
  }]
}
```

---

## 🔄 How Rotation Patterns Are Applied

### Step 1: **Slot Builder Expands Rotations**

The `slot_builder.py` module transforms high-level demands into atomic daily slots:

```python
# From input.json (Nov 1-30, 2025):
demandId: "D_DAY_FRISKING"
rotationSequence: ["D", "D", "D", "D", "D", "O", "O"]
rotationAnchor: "2025-11-01"

# Expands to:
# Nov 1 (Fri): D shift → slot_1
# Nov 2 (Sat): D shift → slot_2
# Nov 3 (Sun): D shift → slot_3
# Nov 4 (Mon): D shift → slot_4
# Nov 5 (Tue): D shift → slot_5
# Nov 6 (Wed): O (off) → [SKIPPED]
# Nov 7 (Thu): O (off) → [SKIPPED]
# Nov 8 (Fri): D shift → slot_6 [PATTERN REPEATS]
# ... and so on for the entire month
```

### Step 2: **Rotation Calculation**

For each day in the planning horizon, the rotation position is calculated:

```python
# For day 2025-11-05 (Nov 5, 2025):
base_date = 2025-11-01  # rotationAnchor
days_since_base = (2025-11-05 - 2025-11-01).days = 4 days
rotation_idx = 4 % 7 = 4  # Position in sequence
shift_code = seq[4] = "D"  # Fifth element (index 4)

# For day 2025-11-06 (Nov 6, 2025):
days_since_base = (2025-11-06 - 2025-11-01).days = 5 days
rotation_idx = 5 % 7 = 5  # Position in sequence
shift_code = seq[5] = "O"  # Sixth element (index 5) = OFF DAY
```

### Step 3: **Slot Creation**

Each non-"O" shift code creates a **Slot** object:

```python
Slot(
    slot_id="D_DAY_FRISKING-2025-11-05-D-abc123",
    demandId="D_DAY_FRISKING",
    date=2025-11-05,
    shiftCode="D",
    start=2025-11-05 08:00,
    end=2025-11-05 20:00,
    headcount=2,                    # Need 2 people
    siteId="SITE-A",                # Site identifier
    ouId="OU-01",                   # Organization unit
    productTypeId="APO",
    rankId="APO",
    preferredTeams=["TEAM-1"],
    whitelist={"employeeIds": [...]}
)
```

---

## 🎯 Site-Based Rotation Pattern (siteId)

### Current Support: **YES** ✅

You can already send shift rotation patterns **grouped by site ID** in your input.json!

### Example: Multiple Sites with Different Rotations

```json
{
  "planningHorizon": {
    "startDate": "2025-11-01",
    "endDate": "2025-11-30"
  },
  "demandItems": [
    {
      "demandId": "D_SITE_A_DAY",
      "siteId": "SITE-A",                        // Site identifier
      "headcount": 2,
      "shiftStartDate": "2025-11-01",
      "shifts": [{
        "shiftDetails": [{"shiftCode": "D", "start": "08:00", "end": "20:00"}],
        "rotationSequence": ["D", "D", "D", "D", "D", "O", "O"],  // 5 days on, 2 off
        "rotationAnchor": "2025-11-01",
        "whitelist": {
          "employeeIds": ["E_ALICE", "E_BOB", "E_CHARLIE"]
        }
      }]
    },
    {
      "demandId": "D_SITE_B_DAY",
      "siteId": "SITE-B",                        // Different site
      "headcount": 3,
      "shiftStartDate": "2025-11-01",
      "shifts": [{
        "shiftDetails": [{"shiftCode": "D", "start": "07:00", "end": "19:00"}],
        "rotationSequence": ["D", "D", "O", "D", "D", "O", "O"],  // Different pattern!
        "rotationAnchor": "2025-11-01",
        "whitelist": {
          "employeeIds": ["E_DIANA", "E_EVA", "E_FRANK", "E_GRACE"]
        }
      }]
    },
    {
      "demandId": "D_SITE_C_NIGHT",
      "siteId": "SITE-C",                        // Another site with night shift
      "headcount": 2,
      "shiftStartDate": "2025-11-01",
      "shifts": [{
        "shiftDetails": [{"shiftCode": "N", "start": "20:00", "end": "08:00", "nextDay": true}],
        "rotationSequence": ["N", "N", "N", "N", "N", "O", "O"],  // Night rotation
        "rotationAnchor": "2025-11-01",
        "whitelist": {
          "employeeIds": ["E_HENRY", "E_IRIS", "E_JACK"]
        }
      }]
    }
  ]
}
```

### Result: Site-Specific Rotations

```
SITE-A:    Day 1-5 work (D), Day 6-7 off (O)     → 5 staff (Alice, Bob, Charlie, Diana, Eva)
SITE-B:    Day 1-2 work (D), Day 3 off (O), ...  → 4 staff (Frank, Grace, Henry, Iris)
SITE-C:    Night 1-5 work (N), Night 6-7 off     → 3 staff (Jack, Karen, Leo)
```

Each site has its own **rotation pattern**, **timing**, and **assigned employees**.

---

## 🧩 Constraint Implementation (S1)

### S1: Rotation Pattern Compliance (Soft Constraint)

The `S1_rotation_pattern.py` module **tracks** rotation compliance:

```python
def add_constraints(model, ctx):
    """
    Soft constraint that encourages rotation pattern compliance.
    
    Key behaviors:
    1. Extracts rotation patterns from demandItems
    2. Maps demandId → rotation sequence + cycle days
    3. Logs rotation information for analysis
    4. Is INFORMATIONAL - rewards compliance but doesn't block solutions
    """
    
    rotation_patterns = {}
    
    for demand in ctx.get('demandItems', []):
        demand_id = demand.get('demandId')
        
        for shift_group in demand.get('shifts', []):
            rotation_seq = shift_group.get('rotationSequence', [])
            cycle_days = shift_group.get('rotationCycleDays', len(rotation_seq))
            anchor = shift_group.get('rotationAnchor')
            
            if rotation_seq:
                rotation_patterns[demand_id] = {
                    'sequence': rotation_seq,
                    'cycle_days': cycle_days,
                    'anchor_date': anchor
                }
    
    # Soft constraint is informational
    # Actual rotation is enforced at slot level
```

**Note**: The rotation patterns are **built into the slots themselves**. The solver doesn't violate them because:
- ✅ Slots are pre-generated following rotation patterns
- ✅ Assignments can only pick from available slots
- ✅ Off-days (O) have no slots to assign

---

## 💾 Input.json Structure for Site-Based Rotations

### Complete Example

```json
{
  "schemaVersion": "0.43",
  "planningHorizon": {
    "startDate": "2025-11-01",
    "endDate": "2025-11-30"
  },
  "demandItems": [
    {
      "demandId": "D_SITE_A_FRISKING",
      "siteId": "SITE-A",                        // ← Site ID
      "ouId": "OU-01",
      "productTypeId": "APO",
      "rankId": "APO",
      "headcount": 2,
      "shiftStartDate": "2025-11-01",
      "shifts": [
        {
          "shiftDetails": [
            {
              "shiftCode": "D",
              "start": "08:00",
              "end": "20:00",
              "nextDay": false
            }
          ],
          "rotationSequence": ["D", "D", "D", "D", "D", "O", "O"],    // ← Pattern
          "rotationCycleDays": 7,
          "rotationAnchor": "2025-11-01",                              // ← Anchor
          "coverage": "FREQ=DAILY;INTERVAL=1",
          "preferredTeams": ["TEAM-A-FRISKING"],
          "whitelist": {
            "teamIds": ["TEAM-A-FRISKING"],
            "employeeIds": [
              "E_ALICE_FRISKING",
              "E_BOB_FRISKING",
              "E_CHARLIE_FRISKING"
            ]
          }
        }
      ]
    },
    {
      "demandId": "D_SITE_B_DETENTION",
      "siteId": "SITE-B",                        // ← Different site
      "ouId": "OU-02",
      "productTypeId": "APO",
      "rankence": 2,
      "shiftStartDate": "2025-11-01",
      "shifts": [
        {
          "shiftDetails": [
            {
              "shiftCode": "N",
              "start": "20:00",
              "end": "08:00",
              "nextDay": true
            }
          ],
          "rotationSequence": ["N", "N", "N", "N", "N", "O", "O"],    // ← Different pattern
          "rotationCycleDays": 7,
          "rotationAnchor": "2025-11-01",
          "coverage": "FREQ=DAILY;INTERVAL=1",
          "preferredTeams": ["TEAM-B-DETENTION"],
          "whitelist": {
            "teamIds": ["TEAM-B-DETENTION"],
            "employeeIds": [
              "E_CAROL_DETENTION",
              "E_DAVID_DETENTION",
              "E_HENRY_DETENTION"
            ]
          }
        }
      ]
    }
  ]
}
```

---

## 🔍 Different Rotation Patterns by Site

### Pattern 1: Classic 5-2 (5 days on, 2 off)
```json
"rotationSequence": ["D", "D", "D", "D", "D", "O", "O"]
"rotationCycleDays": 7
```

### Pattern 2: Alternating Days (3-3)
```json
"rotationSequence": ["D", "D", "D", "O", "O", "O"]
"rotationCycleDays": 6
```

### Pattern 3: Mixed Shifts
```json
"rotationSequence": ["D", "D", "N", "N", "O", "O", "O"]  // Day, Day, Night, Night, Off, Off, Off
"rotationCycleDays": 7
```

### Pattern 4: Shift Handover
```json
"rotationSequence": ["D", "D", "E", "E", "N", "N", "O"]  // Day, Day, Evening, Evening, Night, Night, Off
"rotationCycleDays": 7
```

---

## 📊 How to Query/Filter Rotations by Site

### From the Solver Output

The output includes all assignments with site information:

```json
{
  "assignments": [
    {
      "employeeId": "E_ALICE_FRISKING",
      "demandId": "D_SITE_A_FRISKING",
      "date": "2025-11-01",
      "startDateTime": "2025-11-01T08:00:00",
      "endDateTime": "2025-11-01T20:00:00",
      "siteId": "SITE-A",    // ← Site info embedded
      "ouId": "OU-01"
    },
    {
      "employeeId": "E_CAROL_DETENTION",
      "demandId": "D_SITE_B_DETENTION",
      "date": "2025-11-01",
      "startDateTime": "2025-11-01T20:00:00",
      "endDateTime": "2025-11-02T08:00:00",
      "siteId": "SITE-B",    // ← Different site
      "ouId": "OU-02"
    }
  ]
}
```

### Query by Site in Python

```python
import json

# Load output
with open('output.json') as f:
    result = json.load(f)

# Filter by site
site_a_assignments = [
    a for a in result['assignments'] 
    if a.get('demandId', '').startswith('D_SITE_A_')
]

# Group by employee and site
from collections import defaultdict
by_site = defaultdict(list)
for assignment in result['assignments']:
    demand = assignment['demandId']
    # Extract site from demand ID or use embedded siteId
    site = assignment.get('siteId', 'UNKNOWN')
    by_site[site].append(assignment)

print(f"Site A: {len(by_site['SITE-A'])} assignments")
print(f"Site B: {len(by_site['SITE-B'])} assignments")
print(f"Site C: {len(by_site['SITE-C'])} assignments")
```

---

## ✅ Can You Send Site-Based Rotations in input.json?

### Answer: **YES** ✅

**Current Capability**: Fully supported!

**Implementation Details**:
1. ✅ Each demand item has a `siteId` field
2. ✅ Each demand's shifts define `rotationSequence`
3. ✅ Multiple demands can share the same site (different roles)
4. ✅ Each site can have completely different rotation patterns
5. ✅ The slot builder respects site-specific rotations
6. ✅ Output includes site information

**Example Use Cases**:
- Multiple airports with different shift patterns
- Different terminals with different staffing rotations
- Multiple locations with custom schedules
- Mixed shift types per site (day, evening, night rotations)

---

## 🚀 How to Use Site-Based Rotations

### Step 1: Define Your Sites in input.json

```json
{
  "demandItems": [
    {
      "demandId": "D_AIRPORT_T1_DAY",
      "siteId": "AIRPORT-T1",           // Terminal 1
      "shifts": [{"rotationSequence": ["D","D","D","D","D","O","O"]}]
    },
    {
      "demandId": "D_AIRPORT_T2_DAY",
      "siteId": "AIRPORT-T2",           // Terminal 2 - different pattern!
      "shifts": [{"rotationSequence": ["D","D","D","O","D","D","O"]}]
    },
    {
      "demandId": "D_AIRPORT_T1_NIGHT",
      "siteId": "AIRPORT-T1",           // Terminal 1 night shift
      "shifts": [{"rotationSequence": ["N","N","N","N","N","O","O"]}]
    }
  ]
}
```

### Step 2: Run the Solver

```bash
python run_solver.py --input input.json --output output.json
```

### Step 3: Analyze Results by Site

```python
import json

with open('output.json') as f:
    output = json.load(f)

# Group assignments by site
from collections import defaultdict
by_site = defaultdict(lambda: defaultdict(list))

for assignment in output['assignments']:
    demand_id = assignment['demandId']
    # Extract site from demand ID or use siteId field if available
    site = assignment.get('siteId', 'UNKNOWN')
    emp = assignment['employeeId']
    by_site[site][emp].append(assignment)

# Print per-site summary
for site, staff in sorted(by_site.items()):
    print(f"\n{site}:")
    print(f"  Total staff: {len(staff)}")
    for emp, shifts in staff.items():
        print(f"  {emp}: {len(shifts)} shifts")
```

---

## 📚 Related Files

| File | Purpose |
|---|---|
| `context/engine/slot_builder.py` | Expands rotations into slots |
| `context/constraints/S1_rotation_pattern.py` | Tracks rotation compliance |
| `input_1211_optimized.json` | Example with 3 sites |
| `src/api_server.py` | REST API accepting input.json |
| `run_solver.py` | CLI interface |

---

## 🎯 Summary

✅ **Shift rotation patterns are fully supported**  
✅ **Site-based rotations can be defined in input.json**  
✅ **Each site can have unique shift schedules**  
✅ **Rotation patterns are enforced at the slot level**  
✅ **Output includes site information for filtering**  

The system allows you to submit multiple sites with different rotation patterns in a single input.json file, and the solver will generate optimal schedules respecting each site's unique requirements.

---

**Questions?** Check the documentation files or examine the example input files in the `input/` directory.
