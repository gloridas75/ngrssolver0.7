# Comprehensive Constraint Configuration - input_1211_optimized.json

## Overview

Updated `input_1211_optimized.json` now includes **30 constraints** covering all available constraint types in the NGRS solver:

- **15 Hard Constraints** (must be satisfied for feasibility)
- **15 Soft Constraints** (penalized if violated)

---

## Updated File Structure

### constraintList (30 constraints)

#### Hard Constraints (15)

| # | ID | Description | Parameters |
|---|----|-----------|----|
| 1 | `momDailyHoursCap` | Max daily hours by scheme (A: 14h, B: 13h, P: 9h) | none |
| 2 | `momWeeklyHoursCap44h` | Max 44 weekly normal hours (excludes OT) | `maxWeeklyHours: 44` |
| 3 | `apgdMinRestBetweenShifts` | Minimum rest between consecutive shifts | `minRestMinutes: 660` (11 hours) |
| 4 | `oneShiftPerDay` | Max 1 shift per employee per day | none |
| 5 | `maxConsecutiveWorkingDays` | Max consecutive working days without off-day | `maxConsecutiveDays: 12` |
| 6 | `minimumOffDaysPerWeek` | Minimum off-days per 7-day rolling period | `minOffDaysPerWeek: 1` |
| 7 | `partTimerWeeklyHours` | Part-timer limits (scheme P) | `maxHours4Days: 34.98, maxHoursMoreDays: 29.98` |
| 8 | `licenseValidity` | Check license/qualification expiry dates | none |
| 9 | `skillAndRoleMatch` | Verify required skills and roles present | none |
| 10 | `rankAndProductTypeMatch` | Match rank and product type requirements | none |
| 11 | `slotHeadcount` | Fill all required slot positions | none |
| 12 | `noShiftOverlap` | Prevent overlapping shift assignments | none |
| 13 | `monthlyOtCap72h` | Max monthly OT cap (72h per employee) | `maxMonthlyOtHours: 72` |
| 14 | `genderBalance` | Enforce gender mix for sensitive roles | none |
| 15 | `whitelistBlacklist` | Enforce employee whitelist/blacklist for slots | none |

#### Soft Constraints (15)

| # | ID | Description | Weight in solverScoreConfig |
|---|----|-----------|----|
| 1 | `teamFirstRostering` | Prefer keeping teams together | 5 |
| 2 | `minimizeGapsBetweenAssignedShifts` | Minimize time gaps between consecutive shifts | 1 |
| 3 | `preferredTeamAssignment` | Assign from preferred teams when possible | 3 |
| 4 | `consistentShiftStartTime` | Prefer consistent start times for same employee | 2 |
| 5 | `officerContinuity` | Prefer same officer at site across consecutive days | 4 |
| 6 | `minimizeShiftChangeWithinTeam` | Minimize shift type changes within same team | 2 |
| 7 | `zonePreference` | Honor zone or location preferences | 1 |
| 8 | `teamSizeFeasibility` | Maintain reasonable team sizes | 2 |
| 9 | `fairOvertimeDistribution` | Balance overtime fairly across eligible staff | 3 |
| 10 | `publicHolidayCoverage` | Ensure adequate staffing on public holidays | 4 |
| 11 | `allowanceOptimization` | Optimize allowance capture opportunities | 1 |
| 12 | `substituteLogic` | Apply substitute coverage rules | 2 |
| 13 | `midMonthInsert` | Optimize mid-month roster adjustments | 1 |
| 14 | `demandCoverageScore` | Maximize demand coverage score | 5 |
| 15 | `travelSlackTime` | Account for travel time between locations | 1 |

---

## solverScoreConfig (15 weights)

The updated `solverScoreConfig` now includes weights for all 15 soft constraints:

```json
"solverScoreConfig": {
  "teamFirstRostering": 5,
  "minimizeGapsBetweenAssignedShifts": 1,
  "preferredTeamAssignment": 3,
  "consistentShiftStartTime": 2,
  "officerContinuity": 4,
  "minimizeShiftChangeWithinTeam": 2,
  "zonePreference": 1,
  "teamSizeFeasibility": 2,
  "fairOvertimeDistribution": 3,
  "publicHolidayCoverage": 4,
  "allowanceOptimization": 1,
  "substituteLogic": 2,
  "midMonthInsert": 1,
  "demandCoverageScore": 5,
  "travelSlackTime": 1
}
```

### Weight Interpretation

- **Weight = 1 (Low Priority):** Minimum penalty multiplier
  - `minimizeGapsBetweenAssignedShifts`, `zonePreference`, `allowanceOptimization`, `midMonthInsert`, `travelSlackTime`

- **Weight = 2 (Medium Priority):** 2x penalty multiplier
  - `consistentShiftStartTime`, `minimizeShiftChangeWithinTeam`, `teamSizeFeasibility`, `substituteLogic`

- **Weight = 3 (High Priority):** 3x penalty multiplier
  - `preferredTeamAssignment`, `fairOvertimeDistribution`

- **Weight = 4 (Very High Priority):** 4x penalty multiplier
  - `officerContinuity`, `publicHolidayCoverage`

- **Weight = 5 (Critical Priority):** 5x penalty multiplier
  - `teamFirstRostering`, `demandCoverageScore`

---

## Key Changes from Previous Version

### Before (6 constraints)
```json
"constraintList": [
  {"id": "apgdMinRestBetweenShifts", "enforcement": "hard", "params": {"minRestMinutes": 660}},
  {"id": "oneShiftPerDay", "enforcement": "hard"},
  {"id": "slotHeadcount", "enforcement": "hard"},
  {"id": "momWeeklyHoursCap44h", "enforcement": "hard", "params": {"maxWeeklyHours": 44}},
  {"id": "teamFirstRostering", "enforcement": "soft"},
  {"id": "minimizeGapsBetweenAssignedShifts", "enforcement": "soft"}
]
```

### After (30 constraints)
- Added 9 more hard constraints (total 15)
- Added 13 more soft constraints (total 15)
- Organized with descriptions and parameter documentation
- Added comprehensive `solverScoreConfig` with all 15 soft constraint weights
- All constraints use appropriate enforcement levels

---

## Configuration Notes

### Hard Constraints (Enforcement: "hard")

All hard constraints MUST be satisfied. If any hard constraint is violated, the solver:
- Either finds a different assignment that satisfies it
- Or marks the problem as INFEASIBLE

**Current hard constraints in your file:**
1. Daily and weekly hour limits (MOM regulations)
2. Minimum rest between shifts (APGD compliance)
3. One shift per day per employee
4. Maximum consecutive working days (12)
5. Minimum off-days per week (1)
6. Part-timer hour limits (scheme-specific)
7. License/qualification validity
8. Skill and role matching
9. Rank and product type matching
10. Slot headcount fill
11. No overlapping shifts
12. Monthly OT cap (72h)
13. Gender balance for sensitive roles
14. Whitelist/blacklist enforcement

### Soft Constraints (Enforcement: "soft")

Soft constraints are PENALIZED if violated but don't block solutions.

**Penalty calculation:**
```
Final Penalty = Base Violation Penalty × solverScoreConfig Weight
```

**Example:**
- Constraint: `teamFirstRostering`
- Base penalty: 50 points per violation
- Your weight: 5
- **Final penalty = 50 × 5 = 250 points**

---

## Testing Results

✅ **Input file validated successfully with solver:**

```bash
curl -X POST "http://localhost:8080/solve?time_limit=20" \
     -H "Content-Type: application/json" \
     -d @input/input_1211_optimized.json
```

**Response:**
```json
{
  "status": "OPTIMAL",
  "hard": 0,
  "soft": 0,
  "assignments": 110
}
```

- Status: OPTIMAL ✅
- Hard violations: 0 (all hard constraints satisfied)
- Soft violations: 0 (all soft constraints satisfied)
- Assignments: 110 shifts assigned

---

## How to Use This File

### 1. Adjust Parameters

Modify parameter values based on your business rules:

```json
{
  "id": "apgdMinRestBetweenShifts",
  "enforcement": "hard",
  "params": {"minRestMinutes": 660}  // Change from 660 to 720 for 12-hour minimum
}
```

### 2. Change Enforcement Level

Disable a constraint temporarily or change its level:

```json
{
  "id": "monthlyOtCap72h",
  "enforcement": "disabled"  // Skip this constraint
}
```

Or:

```json
{
  "id": "teamFirstRostering",
  "enforcement": "hard"  // Make it required instead of soft
}
```

### 3. Adjust Soft Constraint Weights

Prioritize constraints by weight:

```json
"solverScoreConfig": {
  "teamFirstRostering": 10,  // Increase priority (from 5)
  "fairOvertimeDistribution": 1  // Decrease priority (from 3)
}
```

---

## Recommendations

### Conservative Setup (Your Current File)

- **Purpose:** Balance all constraints, find optimal solution
- **Hard constraints:** All regulatory/compliance rules
- **Soft constraints:** Weighted to improve operations
- **Result:** OPTIMAL solutions with balanced scoring

### Strict Compliance

If regulatory constraints are critical:

```json
"constraintList": [
  // Keep all hard constraints at "hard"
  {"id": "monthlyOtCap72h", "enforcement": "hard"},
  {"id": "genderBalance", "enforcement": "hard"},
  // Convert some soft to hard if business-critical
  {"id": "teamFirstRostering", "enforcement": "hard"}
]
```

### Relaxed for Feasibility

If getting INFEASIBLE results:

```json
// Disable non-critical constraints
{"id": "officerContinuity", "enforcement": "disabled"},
{"id": "zonePreference", "enforcement": "disabled"},
// Reduce some hard constraints to soft
{"id": "monthlyOtCap72h", "enforcement": "soft"}
```

---

## Files Generated

- ✅ `input/input_1211_optimized.json` - Updated with 30 comprehensive constraints
- ✅ `CONSTRAINT_ARCHITECTURE.md` - Full architecture documentation
- ✅ `API_FIX_SUMMARY.md` - API endpoint fixes

---

## See Also

- `CONSTRAINT_ARCHITECTURE.md` - Complete constraint reference
- `implementation_docs/API/API_DOCUMENTATION.md` - API endpoints
- `context/constraints/*.py` - Individual constraint implementations
