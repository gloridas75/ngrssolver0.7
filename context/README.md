# NGRS Constraint Solver — Context Pack (for Claude Code)

This pack gives Claude the **always-on context** needed to develop the Python **Constraint Solver** for NGRS.

- **Focus**: constraints & solver behavior (not full product UI).
- **Audience**: Python developers building modular CP-SAT/OptaPlanner/Timefold-like constraints.
- **Use**: Load the whole `context/` folder into your IDE/Claude workspace.

## Structure
```
context/
  README.md
  context7.json
  glossary.md
  domain/
    planning_objects.md
    rotation_patterns.md
  engine/
    solver_engine.py
    data_loader.py
    score_helpers.py
  constraints/
    __init__.py
    ... (C1..C16, S1..S16).py
  scoring/
    solverScoreConfig.yaml
  schemas/
    input.schema.json
    output.schema.json
  samples/
    input.sample.json
    output.sample.json
  workflows/
    allowance_approval.md
    bypass_constraint.md
    time_change_approval.md
    exceptions.md
  tests/
    test_constraints_smoke.py
```

## How to use
1. **Read** `domain/` + `schemas/` to understand objects & I/O.
2. **Implement** constraint stubs in `constraints/` (each has a docstring spec).
3. **Tune weights** via `scoring/solverScoreConfig.yaml`.
4. **Run** with `engine/solver_engine.py` against `samples/input.sample.json`.
5. **Verify** with `tests/test_constraints_smoke.py`.

## Notes
- This context distills CAS/Certis hard & soft constraints and delta-solve requirements.
- Keep reruns **non-destructive** (respect published/approved assignments).
