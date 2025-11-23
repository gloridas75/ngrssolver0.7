# NGRS Solver - Complete Input & Output Schemas Documentation

**Schema Version: 0.50**  
**Last Updated: November 14, 2025**

---

## Table of Contents

1. [Overview](#overview)
2. [Input Schema (input_1211_optimized.json)](#input-schema)
3. [Output Schema (output.schema.json)](#output-schema)
4. [Data Types & Enumerations](#data-types--enumerations)
5. [Constraint System](#constraint-system)
6. [Real-World Examples](#real-world-examples)
7. [Validation Rules](#validation-rules)

---

## Overview

The NGRS Solver uses a constraint-based optimization system to generate optimized rosters. The system accepts structured input defining:
- Planning horizon and scheduling parameters
- Employee workforce information
- Demand (shift) requirements
- Constraint definitions and enforcement levels

The solver outputs:
- Optimized assignment roster
- Constraint violation reports
- Hours tracking and validation
- Solution quality metrics

---

## Input Schema

### Root Level Properties

```json
{
  "schemaVersion": "0.50",
  "planningReference": "NGRS_OPTIMAL_MINIMAL_VIOLATIONS",
  "timezone": "Asia/Singapore",
  "planningHorizon": { ... },
  "publicHolidays": [ ... ],
  "solverRunTime": { ... },
  "schemeMap": { ... },
  "constraintList": [ ... ],
  "solverScoreConfig": { ... },
  "demandItems": [ ... ],
  "employees": [ ... ]
}
```

#### `schemaVersion` (string, required)
- Current version: **"0.50"**
- Defines the input/output format version
- Backward compatibility not guaranteed across versions

#### `planningReference` (string, required)
- Unique identifier for the planning scenario
- Format: Free text, recommend: `PROJECT_SCENARIO_VERSION`
- Example: `NGRS_OPTIMAL_MINIMAL_VIOLATIONS`
- Used for audit trails and reference

#### `timezone` (string, required)
- IANA timezone for all time calculations
- Example: `"Asia/Singapore"`, `"UTC"`, `"America/New_York"`
- Must be valid for shift time calculations

#### `planningHorizon` (object, required)
```json
{
  "startDate": "2025-11-01",
  "endDate": "2025-11-30"
}
```
- **startDate** (string, ISO 8601): First day of planning period
- **endDate** (string, ISO 8601): Last day of planning period (inclusive)
- Example: November 1-30, 2025 (30-day period)

#### `publicHolidays` (array, optional)
```json
[
  {
    "date": "2025-12-25",
    "name": "Christmas",
    "includeInRostering": true
  }
]
```
- List of public holidays affecting the planning horizon
- Can be empty `[]` if no holidays apply
- Used for special staffing rules

#### `solverRunTime` (object, required)
```json
{
  "maxSeconds": 600
}
```
- **maxSeconds** (integer): Maximum solver execution time in seconds
- Example: 600 = 10 minutes max run time
- Solver will halt and return best solution found when time expires

#### `schemeMap` (object, required)
```json
{
  "A": "SchemeA",
  "B": "SchemeB",
  "P": "SchemeP"
}
```
- Maps scheme codes to descriptive names
- **A** = Full-time scheme (e.g., 40-44h/week)
- **B** = Full-time scheme variant (e.g., 43h/week)
- **P** = Part-time scheme (e.g., ≤34.98h/week)
- Each employee assigned to exactly one scheme
- Used for hour limits and benefit calculations

---

### Constraint List

```json
"constraintList": [
  {
    "id": "momDailyHoursCap",
    "enforcement": "hard|soft",
    "description": "Constraint description",
    "params": { ... }
  }
]
```

#### Hard Constraints (Must Be Satisfied)
Must not be violated in valid solution or solver returns INFEASIBLE.

| ID | Enforcement | Description | Params |
|---|---|---|---|
| `momDailyHoursCap` | hard | Max daily hours by scheme (A: 14h, B: 13h, P: 9h) | `{}` |
| `momWeeklyHoursCap44h` | hard | Max 44 weekly normal hours | `{"maxWeeklyHours": 44}` |
| `apgdMinRestBetweenShifts` | hard | Min rest between shifts (11h) | `{"minRestMinutes": 660}` |
| `oneShiftPerDay` | hard | Max 1 shift per employee per day | `{}` |
| `maxConsecutiveWorkingDays` | hard | Max 12 consecutive days | `{"maxConsecutiveDays": 12}` |
| `minimumOffDaysPerWeek` | hard | Min 1 off-day per 7 days | `{"minOffDaysPerWeek": 1}` |
| `partTimerWeeklyHours` | hard | Part-time weekly limits | `{"maxHours4Days": 34.98, "maxHoursMoreDays": 29.98}` |
| `licenseValidity` | hard | License/qualification expiry check | `{}` |
| `skillAndRoleMatch` | hard | Required skills present | `{}` |
| `rankAndProductTypeMatch` | hard | Rank matches product type | `{}` |
| `slotHeadcount` | hard | Fill all required positions | `{}` |
| `noShiftOverlap` | hard | Prevent overlapping shifts | `{}` |
| `monthlyOtCap72h` | hard | Max 72h OT per month | `{"maxMonthlyOtHours": 72}` |
| `genderBalance` | hard | Gender mix for sensitive roles | `{}` |
| `whitelistBlacklist` | hard | Employee whitelist/blacklist enforcement | `{}` |

#### Soft Constraints (Optimization Goals)
Violations scored and penalized, but solution can still be OPTIMAL.

| ID | Enforcement | Description |
|---|---|---|
| `teamFirstRostering` | soft | Prefer keeping teams together |
| `minimizeGapsBetweenAssignedShifts` | soft | Minimize time gaps between shifts |
| `preferredTeamAssignment` | soft | Assign from preferred teams |
| `consistentShiftStartTime` | soft | Consistent start times |
| `officerContinuity` | soft | Same officer across consecutive days |
| `minimizeShiftChangeWithinTeam` | soft | Minimize shift type changes |
| `zonePreference` | soft | Honor zone preferences |
| `teamSizeFeasibility` | soft | Maintain reasonable team sizes |
| `fairOvertimeDistribution` | soft | Balance OT across staff |
| `publicHolidayCoverage` | soft | Adequate holiday staffing |
| `allowanceOptimization` | soft | Optimize allowance capture |
| `substituteLogic` | soft | Apply substitute rules |
| `midMonthInsert` | soft | Mid-month adjustments |
| `demandCoverageScore` | soft | Maximize coverage score |
| `travelSlackTime` | soft | Account for travel time |

---

### Solver Score Configuration

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

- **Key**: Soft constraint ID from `constraintList`
- **Value**: Integer weight (1-5, higher = more important)
- Used to optimize soft constraint compliance
- Total penalty calculated as: `Σ(weight × violations)`

**Interpretation:**
- Weight 5: Critical optimization goals (team rostering, coverage score)
- Weight 4: Important business rules (continuity, holiday coverage)
- Weight 1-3: Nice-to-have improvements

---

### Demand Items

```json
"demandItems": [
  {
    "demandId": "D_DAY_FRISKING",
    "siteId": "ChangiT1",
    "ouId": "OU-01",
    "productTypeId": "APO",
    "rankId": "APO",
    "headcount": 2,
    "shiftStartDate": "2025-11-01",
    "shifts": [
      {
        "shiftDetails": [ ... ],
        "rotationSequence": [ ... ],
        "includePublicHolidays": false,
        "includeEveOfPublicHolidays": false,
        "preferredTeams": [ ... ],
        "requiredQualifications": [ ... ],
        "requiredSkills": [ ... ],
        "shiftSetId": "DAY_FRISKING",
        "rotationCycleDays": 7,
        "rotationAnchor": "2025-11-01",
        "weekStartsOn": "MON",
        "whitelist": { ... },
        "slotConstraints": { ... }
      }
    ]
  }
]
```

#### Demand Top-Level

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `demandId` | string | ✓ | Unique demand identifier | `"D_DAY_FRISKING"` |
| `siteId` | string | ✓ | Physical location/site | `"ChangiT1"` |
| `ouId` | string | ✓ | Organizational unit | `"OU-01"` |
| `productTypeId` | string | ✓ | Role type (APO, AVSO, etc.) | `"APO"` |
| `rankId` | string | ✓ | Required rank for demand | `"APO"` |
| `headcount` | integer | ✓ | Positions to fill per shift | `2` |
| `shiftStartDate` | string | ✓ | ISO 8601 start date | `"2025-11-01"` |
| `shifts` | array | ✓ | Shift pattern definitions | See below |

#### Shift Details (Inside `shifts` array)

```json
"shiftDetails": [
  {
    "shiftCode": "D",
    "start": "08:00",
    "end": "20:00",
    "nextDay": false
  }
]
```

- **shiftCode** (string): Identifier (D=Day, N=Night, E=Evening)
- **start** (string): Start time HH:MM (24-hour)
- **end** (string): End time HH:MM (24-hour)
- **nextDay** (boolean): Shift crosses midnight

**Examples:**
- Day shift: `{"shiftCode": "D", "start": "08:00", "end": "20:00", "nextDay": false}`
- Night shift: `{"shiftCode": "N", "start": "20:00", "end": "08:00", "nextDay": true}`

#### Rotation Sequence

```json
"rotationSequence": ["D", "D", "D", "D", "D", "O", "O"]
```

- Array of shift codes or "O" (off-day)
- Repeats cyclically over `rotationCycleDays` period
- Example: DDDDD OO = 5 work days, 2 off-days (7-day cycle)

#### Rotation Parameters

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `rotationCycleDays` | integer | Days in rotation cycle | `7` |
| `rotationAnchor` | string | Start date for cycle (ISO 8601) | `"2025-11-01"` |
| `weekStartsOn` | string | Week start day (MON, SUN, etc.) | `"MON"` |

#### Availability Settings

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `includePublicHolidays` | boolean | Include demand on public holidays | `false` |
| `includeEveOfPublicHolidays` | boolean | Include on holiday eves | `false` |

#### Required Attributes

```json
"requiredQualifications": ["DETENTION-LIC", "XRAY-LIC"],
"requiredSkills": ["detention", "patrol"],
"preferredTeams": ["TEAM-1", "TEAM-2"]
```

- **requiredQualifications** (array): Licenses needed (C7 constraint)
  - Employee must have all listed qualifications
  - C7: License/Qualification Validity enforces this
  
- **requiredSkills** (array): Skills needed
  - C10: Skill/Role Match enforces this
  
- **preferredTeams** (array): Teams to prioritize
  - Not hard constraint, used in soft scoring

#### Shift Set & Identifiers

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `shiftSetId` | string | Unique shift pattern ID | `"DAY_FRISKING"` |
| `shiftCode` | string | Shift type identifier | `"D"` |

#### Whitelist Configuration

```json
"whitelist": {
  "ouIds": [],
  "teamIds": ["TEAM-1"],
  "employeeIds": ["ALICE_FRISKER", "BOB_FRISKER"]
}
```

- **ouIds** (array): Allowed organizational units
- **teamIds** (array): Allowed teams
- **employeeIds** (array): Specific employees eligible
- Empty arrays mean no restriction
- C16: Whitelist/Blacklist enforces this

#### Slot Constraints

```json
"slotConstraints": {
  "genderMix": {
    "requireFemale": true,
    "minFemale": 1
  },
  "roles": []
}
```

- **genderMix**: Gender composition requirements
  - `requireFemale` (boolean): Must have female(s)
  - `minFemale` (integer): Minimum female count
- **roles** (array): Role requirements (extensible)

---

### Employees

```json
"employees": [
  {
    "employeeId": "ALICE_FRISKER",
    "ouId": "OU-01",
    "teamId": "TEAM-1",
    "productTypeId": "APO",
    "rankId": "APO",
    "scheme": "A",
    "rotationOffset": 0,
    "qualifications": [ ... ],
    "skills": [ ... ],
    "gender": "F",
    "licenses": [ ... ],
    "preferences": {},
    "unavailability": []
  }
]
```

#### Employee Properties

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `employeeId` | string | ✓ | Unique identifier | `"ALICE_FRISKER"` |
| `ouId` | string | ✓ | Organizational unit | `"OU-01"` |
| `teamId` | string | ✓ | Team assignment | `"TEAM-1"` |
| `productTypeId` | string | ✓ | Role type | `"APO"` |
| `rankId` | string | ✓ | Rank (C11 matching) | `"APO"` |
| `scheme` | string | ✓ | Work scheme (A, B, P) | `"A"` |
| `rotationOffset` | integer | ✓ | Rotation cycle offset (days) | `0-6` |
| `qualifications` | array | ✓ | List of qualifications | See below |
| `skills` | array | ✓ | List of skills | `["frisking", "patrol"]` |
| `gender` | string | ✓ | Gender (M/F) | `"F"` |
| `licenses` | array | ✓ | Licenses with expiry | See below |
| `preferences` | object | ✓ | Shift preferences | `{}` |
| `unavailability` | array | ✓ | Unavailable dates | `[]` |

#### Qualifications

```json
"qualifications": [
  {
    "code": "FRISKING-LIC",
    "expiryDate": "2026-12-31",
    "status": "active"
  }
]
```

- **code** (string): Qualification identifier
- **expiryDate** (string): ISO 8601 expiry date
- **status** (string): "active", "pending", "expired", etc.
- C7 uses this for license validity checking

#### Licenses

```json
"licenses": [
  {
    "code": "FRISKING-LIC",
    "type": "standard",
    "expiryDate": "2026-12-31"
  }
]
```

- **code** (string): License identifier
- **type** (string): "standard", "provisional", "temporary"
- **expiryDate** (string): ISO 8601 expiry date
- C7 enforces license validity (employee must have required licenses non-expired)

#### Skills

```json
"skills": ["frisking", "patrol", "detention"]
```

- Array of skill identifiers
- C10 matches against demand `requiredSkills`
- Empty array = no special skills

#### Preferences (Optional)

```json
"preferences": {
  "shiftPreference": "D",
  "sitePreference": "ChangiT1"
}
```

- Soft optimization (not enforced)
- Example fields: shift type, location, team preferences
- Used by soft constraint scoring

#### Unavailability (Optional)

```json
"unavailability": [
  {
    "startDate": "2025-11-15",
    "endDate": "2025-11-17",
    "reason": "Annual leave"
  }
]
```

- Dates employee cannot be assigned
- Blocks all assignment attempts on these dates
- Examples: leave, training, suspension

---

## Output Schema

### Root Level Properties

```json
{
  "schemaVersion": "0.50",
  "planningReference": "NGRS_OPTIMAL_MINIMAL_VIOLATIONS",
  "solverRun": { ... },
  "score": { ... },
  "scoreBreakdown": { ... },
  "assignments": [ ... ]
}
```

#### Solver Run Metadata

```json
"solverRun": {
  "runId": "SRN-local-0.4",
  "solverVersion": "optfold-py-0.4.2",
  "startedAt": "2025-11-12T15:02:08.345532",
  "ended": "2025-11-12T15:02:08.389752",
  "durationSeconds": 0.044,
  "status": "OPTIMAL"
}
```

| Field | Type | Description | Values |
|-------|------|-------------|--------|
| `runId` | string | Unique solver run identifier | `"SRN-local-0.4"` |
| `solverVersion` | string | Solver software version | `"optfold-py-0.4.2"` |
| `startedAt` | string | ISO 8601 with microseconds | `"2025-11-12T15:02:08.345532"` |
| `ended` | string | ISO 8601 with microseconds | `"2025-11-12T15:02:08.389752"` |
| `durationSeconds` | float | Total execution time | `0.044` |
| `status` | string | Solution status | `"OPTIMAL"`, `"FEASIBLE"`, `"INFEASIBLE"` |

**Status Meanings:**
- **OPTIMAL**: Best possible solution found satisfying all hard constraints
- **FEASIBLE**: Valid solution found within time limit (may not be best)
- **INFEASIBLE**: No solution satisfies hard constraints

#### Overall Score

```json
"score": {
  "overall": 0,
  "hard": 0,
  "soft": 0
}
```

| Field | Type | Description | Range |
|-------|------|-------------|-------|
| `overall` | integer | Total penalty score | ≥ 0 (lower is better) |
| `hard` | integer | Hard constraint violations | ≥ 0 (must be 0 for valid) |
| `soft` | integer | Soft constraint penalties | ≥ 0 (minimized) |

**Interpretation:**
- If `status: "OPTIMAL"` or `"FEASIBLE"`, then `hard: 0`
- If `status: "INFEASIBLE"`, then `hard > 0`
- Lower `soft` score = better soft constraint compliance

#### Score Breakdown

```json
"scoreBreakdown": {
  "hard": {
    "violations": []
  },
  "soft": {
    "totalPenalty": 0,
    "details": []
  }
}
```

##### Hard Violations

```json
"violations": [
  {
    "constraintId": "momWeeklyHoursCap44h",
    "employeeId": "BETA_005",
    "week": "2025-W45",
    "hoursAssigned": 48,
    "hourlimit": 44,
    "violation": "EXCEEDS"
  }
]
```

- **constraintId** (string): Hard constraint being violated
- **employeeId** (string): Employee with violation
- **details**: Varies by constraint type
- Empty array = no violations (OPTIMAL/FEASIBLE solution)

##### Soft Details

```json
"details": [
  {
    "constraintId": "teamFirstRostering",
    "count": 3,
    "penalty": 15,
    "weight": 5
  }
]
```

- **constraintId** (string): Soft constraint
- **count** (integer): Number of violations
- **penalty** (integer): Count × weight
- **weight** (integer): From solverScoreConfig

---

### Assignments Array

```json
"assignments": [
  {
    "assignmentId": "D_DAY_FRISKING-2025-11-01-D-E_EVA_FRISKER",
    "demandId": "D_DAY_FRISKING",
    "date": "2025-11-01",
    "shiftId": "D",
    "slotId": "D_DAY_FRISKING-2025-11-01-D-be0eb0",
    "shiftCode": "D",
    "startDateTime": "2025-11-01T08:00:00",
    "endDateTime": "2025-11-01T20:00:00",
    "employeeId": "E_EVA_FRISKER",
    "constraintResults": {
      "hard": [],
      "soft": []
    },
    "hours": {
      "gross": 12.0,
      "lunch": 1.0,
      "normal": 8.0,
      "ot": 3.0,
      "paid": 12.0
    }
  }
]
```

#### Assignment Properties

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `assignmentId` | string | Unique assignment ID | `"D_DAY_FRISKING-2025-11-01-D-E_EVA_FRISKER"` |
| `demandId` | string | Demand being fulfilled | `"D_DAY_FRISKING"` |
| `date` | string | Assignment date (ISO 8601) | `"2025-11-01"` |
| `shiftId` | string | Shift type | `"D"` |
| `slotId` | string | Unique slot ID | `"D_DAY_FRISKING-2025-11-01-D-be0eb0"` |
| `shiftCode` | string | Shift code | `"D"` |
| `startDateTime` | string | Shift start (ISO 8601) | `"2025-11-01T08:00:00"` |
| `endDateTime` | string | Shift end (ISO 8601) | `"2025-11-01T20:00:00"` |
| `employeeId` | string | Assigned employee | `"E_EVA_FRISKER"` |
| `constraintResults` | object | Per-assignment violations | See below |
| `hours` | object | Time accounting | See below |

#### Constraint Results (Per Assignment)

```json
"constraintResults": {
  "hard": [
    {
      "constraintId": "licenseValidity",
      "violated": false,
      "details": "License FRISKING-LIC valid"
    }
  ],
  "soft": []
}
```

- **hard** (array): Hard constraint check results
  - `violated` (boolean): Is constraint violated?
  - `details` (string): Explanation
- **soft** (array): Soft constraint check results
  - Similar structure

#### Hours Accounting

```json
"hours": {
  "gross": 12.0,
  "lunch": 1.0,
  "normal": 8.0,
  "ot": 3.0,
  "paid": 12.0
}
```

| Field | Type | Description | Formula |
|-------|------|-------------|---------|
| `gross` | float | Total clock hours | end - start |
| `lunch` | float | Unpaid lunch break | Schedule dependent |
| `normal` | float | Normal hours (no OT) | gross - lunch - ot |
| `ot` | float | Overtime hours | gross - lunch - normal |
| `paid` | float | Total paid hours | normal + ot |

**Example Calculation (08:00-20:00):**
- Gross: 12h
- Lunch: -1h (unpaid)
- Paid: 11h → 8h normal + 3h OT

**Hour Category Thresholds:**
- Hours 1-8: Normal rate
- Hours 9+: Overtime rate

---

## Data Types & Enumerations

### Date/Time Formats

| Format | Example | Usage |
|--------|---------|-------|
| ISO 8601 Date | `2025-11-01` | Planning horizon dates |
| ISO 8601 DateTime | `2025-11-01T08:00:00` | Shift times |
| ISO 8601 DateTime + μs | `2025-11-12T15:02:08.345532` | Solver timestamps |
| ISO Week | `2025-W45` | Weekly constraint reporting |
| HH:MM (24-hour) | `08:00`, `20:00` | Shift start/end |

### Enumerations

#### Employee Schemes
```
"A" = SchemeA (full-time, 44h/week limit)
"B" = SchemeB (full-time variant, 43h/week)
"P" = SchemeP (part-time, ≤34.98h/week limit)
```

#### Shift Codes
```
"D" = Day shift (typically 08:00-20:00)
"N" = Night shift (typically 20:00-08:00, nextDay: true)
"E" = Evening shift (optional, e.g., 15:00-23:00)
"O" = Off-day (no shift)
```

#### Product Types (Rank Matching - C11)
```
"APO" = Airport Police Officer
"AVSO" = Airport VSO (Aviation Security Officer)
"CVSO" = Civil VSO (Civil Security Officer)
```

#### Enforcement Levels
```
"hard" = Must be satisfied (INFEASIBLE if violated)
"soft" = Optimization goal (OPTIMAL/FEASIBLE even if violated)
```

#### Solver Status
```
"OPTIMAL" = Best possible solution, all hard constraints satisfied
"FEASIBLE" = Valid solution found, all hard constraints satisfied
"INFEASIBLE" = No solution satisfies all hard constraints
"MODEL_INVALID" = Model definition error
```

#### Gender
```
"M" = Male
"F" = Female
"X" = Other/Not specified
```

#### License Status
```
"active" = Currently valid
"pending" = Awaiting approval
"expired" = No longer valid
"suspended" = Temporarily unavailable
```

---

## Constraint System

### Hard Constraints (MUST SATISFY)

#### C1: Daily Hours Constraint
- **ID**: `momDailyHoursCap`
- **Enforcement**: Hard
- **Rule**: Max gross hours per shift by scheme
  - Scheme A: ≤14h gross
  - Scheme B: ≤13h gross
  - Scheme P: ≤9h gross
- **Implementation**: Per-shift validation
- **Violation Example**: Day shift 08:00-23:00 = 15h gross > 14h limit

#### C2: Weekly & Monthly Hours Constraints
- **ID**: `momWeeklyHoursCap44h`, `monthlyOtCap72h`
- **Enforcement**: Hard
- **Rules**:
  - Weekly normal hours ≤44h (excludes OT)
  - Monthly OT hours ≤72h per employee
- **Grouping**: ISO weeks and calendar months
- **Implementation**: Integer scaled constraints (×10)
- **Violation Example**: 48h normal hours in week 45 (exceeds 44h)

#### C3: Minimum Rest Between Shifts
- **ID**: `apgdMinRestBetweenShifts`
- **Enforcement**: Hard
- **Rule**: ≥11 hours (660 minutes) between shift end and next start
- **Implementation**: Disjunctive constraints
- **Violation Example**: Shift ends 20:00, next starts 06:00 = 10h gap

#### C4: One Shift Per Day
- **ID**: `oneShiftPerDay`
- **Enforcement**: Hard
- **Rule**: Max 1 shift per employee per calendar day
- **Implementation**: Sum constraints
- **Violation Example**: Employee assigned to both Day and Evening on same date

#### C5: Maximum Consecutive Working Days
- **ID**: `maxConsecutiveWorkingDays`
- **Enforcement**: Hard
- **Rule**: ≤12 consecutive days (must have ≥1 off-day)
- **Implementation**: Rolling window validation
- **Violation Example**: 13 consecutive days without off-day

#### C6: Minimum Off-Days Per Week
- **ID**: `minimumOffDaysPerWeek`
- **Enforcement**: Hard
- **Rule**: ≥1 off-day per 7-day rolling period
- **Implementation**: Per-7-day-window validation
- **Violation Example**: Working all 7 days of a week

#### C7: License/Qualification Validity
- **ID**: `licenseValidity`
- **Enforcement**: Hard
- **Rule**: Employee must have ALL required qualifications non-expired
- **Implementation**: model.Add(var == 0) for unlicensed employees
- **Violation Example**: Shift requires DETENTION-LIC but employee lacks it or expired
- **Check**: Compares assignment date against license expiryDate

#### C8: Skill and Role Match
- **ID**: `skillAndRoleMatch`
- **Enforcement**: Hard
- **Rule**: Employee must have ALL required skills
- **Implementation**: Whitelist/blacklist at model level
- **Violation Example**: Demand requires "xray" skill but employee lacks it

#### C9: Rank and Product Type Match
- **ID**: `rankAndProductTypeMatch`
- **Enforcement**: Hard
- **Rule**: Employee rank MUST EQUAL demand productTypeId
- **Implementation**: model.Add(var == 0) for mismatched ranks
- **Violation Example**: AVSO employee (rankId=AVSO) cannot work APO demand (productTypeId=APO)
- **Ranks**: APO, AVSO, CVSO (no cross-assignment)

#### C10: Slot Headcount
- **ID**: `slotHeadcount`
- **Enforcement**: Hard
- **Rule**: Each shift slot must have exactly `headcount` assignments
- **Implementation**: Sum constraints per slot
- **Violation Example**: Demand D_FRISKING requires 2 people but only 1 assigned

#### C11: No Shift Overlap
- **ID**: `noShiftOverlap`
- **Enforcement**: Hard
- **Rule**: Shifts cannot overlap (covered by C3 rest period)
- **Implementation**: Disjunctive constraints
- **Violation Example**: 08:00-20:00 and 18:00-02:00 overlap by 2 hours

#### C12: Monthly OT Cap
- **ID**: `monthlyOtCap72h`
- **Enforcement**: Hard
- **Rule**: OT hours per employee ≤72h per calendar month
- **Implementation**: Integer scaled (×10), grouped by emp-month
- **Violation Example**: 80h OT in November > 72h cap

#### C13: Gender Balance
- **ID**: `genderBalance`
- **Enforcement**: Hard
- **Rule**: Gender composition as required by demand
- **Implementation**: Constraint per slot with gender requirements
- **Violation Example**: Frisking demand requires ≥1 female, all assigned are male

#### C14: Whitelist/Blacklist
- **ID**: `whitelistBlacklist`
- **Enforcement**: Hard
- **Rule**: Only whitelisted employees can be assigned to whitelisted slots
- **Implementation**: Decision variables only created for whitelisted pairs
- **Violation Example**: Employee not in TEAM-1 assigned to TEAM-1 only slot

### Soft Constraints (OPTIMIZATION GOALS)

| ID | Weight | Goal | Score |
|---|---|---|---|
| `teamFirstRostering` | 5 | Keep teams together | High priority |
| `officerContinuity` | 4 | Same officer consecutive days | High priority |
| `publicHolidayCoverage` | 4 | Adequate holiday staffing | High priority |
| `demandCoverageScore` | 5 | Maximize coverage | Critical |
| `fairOvertimeDistribution` | 3 | Balanced OT | Medium |
| `preferredTeamAssignment` | 3 | Use preferred teams | Medium |
| `minimizeGapsBetweenAssignedShifts` | 1 | Short gaps between shifts | Low |
| `consistentShiftStartTime` | 2 | Consistent start times | Medium |
| `minimizeShiftChangeWithinTeam` | 2 | Stable shift types | Medium |
| `teamSizeFeasibility` | 2 | Reasonable team sizes | Medium |
| `zonePreference` | 1 | Honor location preferences | Low |
| `allowanceOptimization` | 1 | Maximize allowances | Low |
| `substituteLogic` | 2 | Apply substitute rules | Medium |
| `midMonthInsert` | 1 | Mid-month adjustments | Low |
| `travelSlackTime` | 1 | Account for travel | Low |

---

## Real-World Examples

### Example 1: Standard Day Shift Demand

```json
{
  "demandId": "D_PATROL_DAY",
  "siteId": "ChangiT1",
  "ouId": "OU-PATROL",
  "productTypeId": "APO",
  "rankId": "APO",
  "headcount": 2,
  "shiftStartDate": "2025-11-01",
  "shifts": [{
    "shiftDetails": [{
      "shiftCode": "D",
      "start": "08:00",
      "end": "20:00",
      "nextDay": false
    }],
    "rotationSequence": ["D", "D", "D", "D", "D", "O", "O"],
    "includePublicHolidays": false,
    "includeEveOfPublicHolidays": false,
    "preferredTeams": ["TEAM-PATROL"],
    "requiredQualifications": [],
    "requiredSkills": ["patrol"],
    "shiftSetId": "PATROL_DAY",
    "rotationCycleDays": 7,
    "rotationAnchor": "2025-11-01",
    "weekStartsOn": "MON",
    "whitelist": {
      "ouIds": [],
      "teamIds": ["TEAM-PATROL"],
      "employeeIds": []
    },
    "slotConstraints": {
      "genderMix": {},
      "roles": []
    }
  }]
}
```

**Interpretation:**
- Patrol function, 2 officers per day
- 5-day work, 2-day off rotation
- Only from TEAM-PATROL
- Any APO rank, any gender
- No license required (general patrol)

### Example 2: Specialized Frisking with Gender Requirements

```json
{
  "demandId": "D_FRISKING",
  "siteId": "ChangiT1",
  "ouId": "OU-01",
  "productTypeId": "APO",
  "rankId": "APO",
  "headcount": 3,
  "shiftStartDate": "2025-11-01",
  "shifts": [{
    "shiftDetails": [{
      "shiftCode": "D",
      "start": "08:00",
      "end": "20:00",
      "nextDay": false
    }],
    "rotationSequence": ["D", "D", "D", "D", "D", "O", "O"],
    "includePublicHolidays": false,
    "includeEveOfPublicHolidays": false,
    "preferredTeams": ["TEAM-FRISKING"],
    "requiredQualifications": ["FRISKING-LIC"],
    "requiredSkills": ["frisking"],
    "shiftSetId": "FRISKING_DAY",
    "rotationCycleDays": 7,
    "rotationAnchor": "2025-11-01",
    "weekStartsOn": "MON",
    "whitelist": {
      "ouIds": [],
      "teamIds": ["TEAM-FRISKING"],
      "employeeIds": ["ALICE_FRISKER", "BOB_FRISKER", "DIANA_FRISKER"]
    },
    "slotConstraints": {
      "genderMix": {
        "requireFemale": true,
        "minFemale": 2
      },
      "roles": []
    }
  }]
}
```

**Constraints Triggered:**
- C7: FRISKING-LIC required (hard constraint)
- C10: "frisking" skill required (hard constraint)
- C13: ≥2 female officers per slot (hard constraint)
- C14: Only whitelisted 3 employees can be assigned (hard constraint)

### Example 3: Employee with Multiple Qualifications

```json
{
  "employeeId": "SPECIALIST_001",
  "ouId": "OU-01",
  "teamId": "TEAM-MULTI",
  "productTypeId": "APO",
  "rankId": "APO",
  "scheme": "A",
  "rotationOffset": 1,
  "qualifications": [
    {
      "code": "FRISKING-LIC",
      "expiryDate": "2026-12-31",
      "status": "active"
    },
    {
      "code": "DETENTION-LIC",
      "expiryDate": "2026-06-30",
      "status": "active"
    },
    {
      "code": "XRAY-LIC",
      "expiryDate": "2025-05-15",
      "status": "expired"
    }
  ],
  "skills": ["frisking", "detention", "patrol"],
  "gender": "F",
  "licenses": [
    {
      "code": "FRISKING-LIC",
      "type": "standard",
      "expiryDate": "2026-12-31"
    },
    {
      "code": "DETENTION-LIC",
      "type": "standard",
      "expiryDate": "2026-06-30"
    },
    {
      "code": "XRAY-LIC",
      "type": "standard",
      "expiryDate": "2025-05-15"
    }
  ],
  "preferences": {
    "shiftPreference": "D"
  },
  "unavailability": [
    {
      "startDate": "2025-11-01",
      "endDate": "2025-11-05",
      "reason": "Annual leave"
    }
  ]
}
```

**Assignment Eligibility:**
- ✓ Can work: Frisking (LIC active), Detention (LIC active), Patrol (no LIC needed)
- ✗ Cannot work: XRAY (LIC expired as of 2025-05-15)
- ✗ Unavailable: Nov 1-5 (annual leave blocks all assignments)
- → Available from Nov 6, 2025 onwards
- → Can be assigned to any demand requiring frisking, detention, or patrol skills

---

## Validation Rules

### Input Validation

#### Required Fields
Every object must have its required fields or input is REJECTED:
- Demand: `demandId`, `productTypeId`, `rankId`, `headcount`, `shifts`
- Employee: `employeeId`, `rankId`, `scheme`, `qualifications`, `licenses`
- Shift: `shiftDetails`, `rotationSequence`, `rotationCycleDays`

#### Date Validations
```
- planningHorizon.startDate < planningHorizon.endDate
- All dates ISO 8601 format (YYYY-MM-DD)
- shiftStartDate within planningHorizon
- License expiryDate must be in future (or past for expired)
```

#### Time Validations
```
- Shift start/end in HH:MM format (00:00-23:59)
- If nextDay=false: start < end
- If nextDay=true: shift crosses midnight correctly
- shiftDetails times consistent (08:00-20:00 = 12h)
```

#### Enum Validations
```
- scheme ∈ {"A", "B", "P"}
- shiftCode ∈ {"D", "N", "E", "O", ...}
- enforcement ∈ {"hard", "soft"}
- gender ∈ {"M", "F", "X"}
- productTypeId must match rankId possibilities
```

#### Range Validations
```
- headcount ≥ 1
- rotationCycleDays ≥ 1
- rotationOffset 0 ≤ rotationOffset < rotationCycleDays
- maxSeconds ≥ 1
```

#### Data Integrity
```
- employeeId unique within employees array
- demandId unique within demandItems array
- constraintList IDs unique
- Whitelist employee IDs must exist in employees array
- requiredQualifications must have matching license codes in at least some employees
- requiredSkills must have matching skills in at least some employees
```

### Output Validation

#### Status Consistency
```
IF status = "OPTIMAL" THEN hard violations = 0
IF status = "FEASIBLE" THEN hard violations = 0
IF status = "INFEASIBLE" THEN hard violations > 0
```

#### Assignment Completeness
```
All demand headcount positions filled (or INFEASIBLE)
Each slot has exactly headcount assignments
No employee double-assigned on same day
```

#### Hours Consistency
```
gross = endDateTime - startDateTime
paid = normal + ot
normal + ot + lunch = gross
normal ≤ 8 hours for standard 8h shifts
```

#### Score Consistency
```
overall = hard + soft
hard = 0 for OPTIMAL/FEASIBLE status
soft ≥ 0
Each soft detail penalty = count × weight
```

---

## Appendix: Common Patterns

### Pattern 1: Full Month Roster (30 days)
```json
"planningHorizon": {
  "startDate": "2025-11-01",
  "endDate": "2025-11-30"
}
```

### Pattern 2: Two-Week Sprint
```json
"planningHorizon": {
  "startDate": "2025-11-01",
  "endDate": "2025-11-14"
}
```

### Pattern 3: Standard 5-Day / 2-Day Rotation
```json
"rotationSequence": ["D", "D", "D", "D", "D", "O", "O"],
"rotationCycleDays": 7,
"rotationAnchor": "2025-11-01"
```

### Pattern 4: 4-Day / 3-Day Rotation
```json
"rotationSequence": ["D", "D", "D", "D", "O", "O", "O"],
"rotationCycleDays": 7,
"rotationAnchor": "2025-11-01"
```

### Pattern 5: 3-Shift Rotation (Day/Night/Off)
```json
"rotationSequence": ["D", "N", "O"],
"rotationCycleDays": 3,
"rotationAnchor": "2025-11-01"
```

---

**End of Documentation**

**For questions or clarifications, refer to:**
- `context/schemas/input.schema.json` (JSON schema definitions)
- `context/schemas/output.schema.json` (Example output)
- `implementation_docs/` (Additional implementation guides)
