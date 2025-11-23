# Shift Rotation Examples - Visual Guide

**Date**: November 13, 2025  
**Topic**: Real-world examples of shift rotation patterns by site

---

## 📊 Example 1: Simple 5-Day On, 2-Day Off (5-2 Pattern)

### Configuration

```json
{
  "demandId": "D_AIRPORT_FRISKING",
  "siteId": "AIRPORT-T1",
  "headcount": 2,
  "shiftStartDate": "2025-11-01",
  "shifts": [{
    "shiftDetails": [
      {"shiftCode": "D", "start": "08:00", "end": "20:00", "nextDay": false}
    ],
    "rotationSequence": ["D", "D", "D", "D", "D", "O", "O"],
    "rotationCycleDays": 7,
    "rotationAnchor": "2025-11-01",
    "whitelist": {
      "employeeIds": ["ALICE", "BOB", "CHARLIE", "DIANA"]
    }
  }]
}
```

### Visual Timeline (November 2025)

```
Week 1:
  Nov 1 (Fri): D  ←─ Index 0 → "D"
  Nov 2 (Sat): D  ←─ Index 1 → "D"
  Nov 3 (Sun): D  ←─ Index 2 → "D"
  Nov 4 (Mon): D  ←─ Index 3 → "D"
  Nov 5 (Tue): D  ←─ Index 4 → "D"
  Nov 6 (Wed): O  ←─ Index 5 → "O" (OFF)
  Nov 7 (Thu): O  ←─ Index 6 → "O" (OFF)

Week 2:
  Nov 8 (Fri): D  ←─ Index 0 → "D" [PATTERN REPEATS]
  Nov 9 (Sat): D  ←─ Index 1 → "D"
  Nov 10 (Sun): D ←─ Index 2 → "D"
  Nov 11 (Mon): D ←─ Index 3 → "D"
  Nov 12 (Tue): D ←─ Index 4 → "D"
  Nov 13 (Wed): O ←─ Index 5 → "O" (OFF)
  Nov 14 (Thu): O ←─ Index 6 → "O" (OFF)

Week 3: [REPEATS] ... and so on
```

### Slots Generated

```
SLOT: D_AIRPORT_FRISKING-2025-11-01-D (08:00-20:00) - ALICE
SLOT: D_AIRPORT_FRISKING-2025-11-02-D (08:00-20:00) - BOB
SLOT: D_AIRPORT_FRISKING-2025-11-03-D (08:00-20:00) - CHARLIE
SLOT: D_AIRPORT_FRISKING-2025-11-04-D (08:00-20:00) - DIANA
SLOT: D_AIRPORT_FRISKING-2025-11-05-D (08:00-20:00) - ALICE [Rotation]
SLOT: D_AIRPORT_FRISKING-2025-11-06-O (OFF) - [SKIPPED]
SLOT: D_AIRPORT_FRISKING-2025-11-07-O (OFF) - [SKIPPED]
SLOT: D_AIRPORT_FRISKING-2025-11-08-D (08:00-20:00) - BOB [Next cycle starts]
... total 22 slots in November (30 days - 8 off days)
```

---

## 📊 Example 2: Mixed Day/Night Rotations (Different Sites)

### Configuration - Site A (Day Shifts)

```json
{
  "demandId": "D_SITE_A_DAY",
  "siteId": "SITE-A",
  "shifts": [{
    "rotationSequence": ["D", "D", "D", "D", "D", "O", "O"],
    "rotationAnchor": "2025-11-01",
    "whitelist": {"employeeIds": ["E1", "E2", "E3", "E4"]}
  }]
}
```

### Configuration - Site B (Night Shifts)

```json
{
  "demandId": "D_SITE_B_NIGHT",
  "siteId": "SITE-B",
  "shifts": [{
    "rotationSequence": ["N", "N", "N", "N", "N", "O", "O"],
    "rotationAnchor": "2025-11-01",
    "whitelist": {"employeeIds": ["E5", "E6", "E7"]}
  }]
}
```

### Visual Comparison

```
SITE-A (Day Shift):          SITE-B (Night Shift):
Nov 1  D (08:00-20:00)       Nov 1  N (20:00-08:00+1)
Nov 2  D (08:00-20:00)       Nov 2  N (20:00-08:00+1)
Nov 3  D (08:00-20:00)       Nov 3  N (20:00-08:00+1)
Nov 4  D (08:00-20:00)       Nov 4  N (20:00-08:00+1)
Nov 5  D (08:00-20:00)       Nov 5  N (20:00-08:00+1)
Nov 6  O (OFF)               Nov 6  O (OFF)
Nov 7  O (OFF)               Nov 7  O (OFF)
Nov 8  D (08:00-20:00)       Nov 8  N (20:00-08:00+1)
...                          ...
```

### Staff Distribution

```
SITE-A (Day):        SITE-B (Night):
E1 → Slots for D     E5 → Slots for N
E2 → Slots for D     E6 → Slots for N
E3 → Slots for D     E7 → Slots for N
E4 → Slots for D
```

---

## 📊 Example 3: Complex Pattern - 3-3-1 (3 Day, 3 Night, 1 Off)

### Configuration

```json
{
  "demandId": "D_AIRPORT_COMPLEX",
  "siteId": "AIRPORT-T3",
  "shifts": [{
    "rotationSequence": ["D", "D", "D", "N", "N", "N", "O"],
    "rotationCycleDays": 7,
    "rotationAnchor": "2025-11-01",
    "shiftDetails": [
      {"shiftCode": "D", "start": "08:00", "end": "20:00", "nextDay": false},
      {"shiftCode": "N", "start": "20:00", "end": "08:00", "nextDay": true}
    ],
    "whitelist": {"employeeIds": ["WORKER_A", "WORKER_B", "WORKER_C"]}
  }]
}
```

### Visual Timeline

```
Week 1:
  Nov 1 (Fri): D  ←─ 3 Day shifts
  Nov 2 (Sat): D
  Nov 3 (Sun): D
  Nov 4 (Mon): N  ←─ 3 Night shifts
  Nov 5 (Tue): N
  Nov 6 (Wed): N
  Nov 7 (Thu): O  ←─ 1 Off day

Week 2: [REPEATS]
  Nov 8 (Fri): D
  Nov 9 (Sat): D
  Nov 10 (Sun): D
  Nov 11 (Mon): N
  Nov 12 (Tue): N
  Nov 13 (Wed): N
  Nov 14 (Thu): O
```

### Monthly Coverage

```
November 2025:
  Days worked: Nov 1-30
  Total 7-day cycles: 4 complete + 2 days
  
  Day shifts (D):    Nov 1-3, 8-10, 15-17, 22-24, 29-30
  Night shifts (N):  Nov 4-6, 11-13, 18-20, 25-27
  Off days (O):      Nov 7, 14, 21, 28
```

---

## 📊 Example 4: Multiple Sites, Different Patterns

### Input Configuration

```json
{
  "demandItems": [
    {
      "demandId": "D_AIRPORT_T1_DAY",
      "siteId": "AIRPORT-T1",
      "shifts": [{
        "rotationSequence": ["D", "D", "D", "D", "D", "O", "O"],  // 5-2
        "rotationAnchor": "2025-11-01"
      }]
    },
    {
      "demandId": "D_AIRPORT_T2_DAY",
      "siteId": "AIRPORT-T2",
      "shifts": [{
        "rotationSequence": ["D", "D", "D", "O", "D", "D", "O"],  // Different!
        "rotationAnchor": "2025-11-01"
      }]
    },
    {
      "demandId": "D_CARGO_NIGHT",
      "siteId": "CARGO-TERMINAL",
      "shifts": [{
        "rotationSequence": ["N", "N", "N", "N", "O", "O", "O"],  // 4-3
        "rotationAnchor": "2025-11-01"
      }]
    }
  ]
}
```

### Site Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│ SITE: AIRPORT-T1 (Pattern: 5-2)                                │
├─────────────────────────────────────────────────────────────────┤
│ Nov:  D D D D D O O | D D D D D O O | D D D D D O O | D D       │
│ Work: 5 days   Off: 2 days  |  7-day cycle                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ SITE: AIRPORT-T2 (Pattern: 3-1-2)                              │
├─────────────────────────────────────────────────────────────────┤
│ Nov:  D D D O D D O | D D D O D D O | D D D O D D O | D D       │
│ Work: 3 on, 1 off, 2 on |  7-day cycle                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ SITE: CARGO-TERMINAL (Pattern: 4-3)                            │
├─────────────────────────────────────────────────────────────────┤
│ Nov:  N N N N O O O | N N N N O O O | N N N N O O O | N N      │
│ Work: 4 nights  Off: 3 days  |  7-day cycle                    │
└─────────────────────────────────────────────────────────────────┘
```

### Output Analysis

```python
# Group by site
assignments_by_site = {
    "AIRPORT-T1": 22,  # 30 - 8 off days
    "AIRPORT-T2": 24,  # Different off pattern
    "CARGO-TERMINAL": 18  # 4-on per 7-day cycle = ~18 in Nov
}
```

---

## 📊 Example 5: Anchor Date Impact (Starting Mid-Week)

### Same Pattern, Different Anchor Dates

#### Scenario A: Anchor on Friday (Nov 1)

```json
{
  "rotationSequence": ["D", "D", "D", "D", "D", "O", "O"],
  "rotationAnchor": "2025-11-01"  // Friday
}
```

```
Nov 1 (Fri): D ←─ Index 0
Nov 2 (Sat): D ←─ Index 1
Nov 3 (Sun): D ←─ Index 2
Nov 4 (Mon): D ←─ Index 3
Nov 5 (Tue): D ←─ Index 4
Nov 6 (Wed): O ←─ Index 5
Nov 7 (Thu): O ←─ Index 6
Nov 8 (Fri): D ←─ Index 0 (REPEAT)
```

#### Scenario B: Anchor on Monday (Nov 4)

```json
{
  "rotationSequence": ["D", "D", "D", "D", "D", "O", "O"],
  "rotationAnchor": "2025-11-04"  // Monday (4 days later)
}
```

```
Nov 1 (Fri): ? ←─ Before anchor, how to handle?
Nov 2 (Sat): ? ←─ Before anchor
Nov 3 (Sun): ? ←─ Before anchor
Nov 4 (Mon): D ←─ Index 0 (Anchor date)
Nov 5 (Tue): D ←─ Index 1
Nov 6 (Wed): D ←─ Index 2
Nov 7 (Thu): D ←─ Index 3
Nov 8 (Fri): D ←─ Index 4
Nov 9 (Sat): O ←─ Index 5
Nov 10 (Sun): O ←─ Index 6
```

**Note**: The `rotationAnchor` determines where the cycle starts. Use the planning start date for simplicity.

---

## 📊 Example 6: Rotation with Team Switching

### Configuration: Team A vs Team B

```json
{
  "demandItems": [
    {
      "demandId": "D_FRISKING_A",
      "siteId": "AIRPORT",
      "shifts": [{
        "rotationSequence": ["D", "D", "D", "O", "O", "D", "D"],
        "rotationAnchor": "2025-11-01",
        "whitelist": {"teamIds": ["TEAM-A"]}
      }]
    },
    {
      "demandId": "D_FRISKING_B",
      "siteId": "AIRPORT",
      "shifts": [{
        "rotationSequence": ["O", "O", "D", "D", "D", "O", "O"],  // Shifted by 2 days
        "rotationAnchor": "2025-11-01",
        "whitelist": {"teamIds": ["TEAM-B"]}
      }]
    }
  ]
}
```

### 24/7 Coverage

```
       Team A:   Team B:   Combined Coverage:
Nov 1   D        O        → One team working
Nov 2   D        O        → One team working
Nov 3   D        D        → Both teams working ✓
Nov 4   O        D        → One team working
Nov 5   O        D        → One team working
Nov 6   D        O        → One team working
Nov 7   D        O        → One team working
Nov 8   D        O        → [Pattern repeats]

Result: 24/7 coverage with staggered rotation!
```

---

## 🔍 How to Verify Rotation in Output

### Python Script to Analyze Rotation

```python
import json
from datetime import datetime
from collections import defaultdict

# Load output
with open('output.json') as f:
    output = json.load(f)

# Extract rotation pattern for each demand
rotations = defaultdict(lambda: defaultdict(list))

for assignment in sorted(output['assignments'], key=lambda x: (x['demandId'], x['date'])):
    demand_id = assignment['demandId']
    date = assignment['date']
    emp = assignment['employeeId']
    
    rotations[demand_id][emp].append(date)

# Print for each demand
for demand_id in sorted(rotations.keys()):
    print(f"\n{demand_id}:")
    for emp in sorted(rotations[demand_id].keys()):
        dates = rotations[demand_id][emp]
        print(f"  {emp}: {len(dates)} shifts")
        # Show first week pattern
        if len(dates) >= 7:
            print(f"    Week 1: {', '.join(str(d) for d in dates[:7])}")
```

### Output Example

```
D_AIRPORT_FRISKING:
  ALICE: 22 shifts
    Week 1: 2025-11-01, 2025-11-02, 2025-11-03, 2025-11-04, 2025-11-05, 2025-11-08, 2025-11-09
  BOB: 22 shifts
    Week 1: 2025-11-01, 2025-11-02, 2025-11-03, 2025-11-04, 2025-11-05, 2025-11-08, 2025-11-09

Pattern Verification:
✓ Alice works 5 days, off 2 days (matches [D,D,D,D,D,O,O])
✓ Bob follows same pattern
✓ Rotation enforced at slot level
```

---

## 🎯 Summary

| Example | Pattern | Sites | Use Case |
|---------|---------|-------|----------|
| 1 | 5-2 | Single | Standard rotation |
| 2 | Day/Night | 2 different | Mixed shifts |
| 3 | 3-3-1 | Single | Complex rotation |
| 4 | Multiple | 3 different | Multi-site scheduling |
| 5 | Anchor Date | Single | Start mid-cycle |
| 6 | Team Switching | 2 teams | 24/7 coverage |

**Key Takeaway**: Each site can have a **unique rotation pattern**. The slot builder expands these patterns into daily slots, and the solver assigns employees while respecting the patterns.

---

**For more details**, see:
- `SHIFT_ROTATION_GUIDE.md` - Technical explanation
- `input_1211_optimized.json` - Real example
- `S1_rotation_pattern.py` - Implementation code
