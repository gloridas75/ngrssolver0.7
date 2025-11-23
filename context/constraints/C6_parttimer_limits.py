"""C6: Part-time employee weekly hour limits (HARD constraint).

Enforce that part-time employees (Scheme P) do not exceed their weekly working hour limits.
Scheme P has two-tier limits based on number of working days:
- ≤4 working days per week: max 34.98 hours
- >4 working days per week: max 29.98 hours
"""
from collections import defaultdict
from datetime import datetime


def add_constraints(model, ctx):
    """
    Enforce weekly hour limits for Scheme P (part-time) employees (HARD).
    
    Strategy: 
    1. Identify Scheme P employees
    2. For each week, create day-worked indicator variables
    3. Add conditional constraints based on working days:
       - If working_days <= 4: hours <= 34.98
       - If working_days > 4: hours <= 29.98
    
    Args:
        model: CP-SAT model
        ctx: Context dict with 'slots', 'employees', 'x'
    """
    
    slots = ctx.get('slots', [])
    employees = ctx.get('employees', [])
    x = ctx.get('x', {})
    
    if not slots or not x or not employees:
        print(f"[C6] Warning: Slots, employees, or decision variables not available")
        return
    
    # Identify Scheme P (part-time) employees
    scheme_p_employees = []
    for emp in employees:
        emp_id = emp.get('employeeId')
        scheme = emp.get('scheme', '')
        if scheme == 'P':
            scheme_p_employees.append(emp_id)
    
    if not scheme_p_employees:
        print(f"[C6] Part-Time Employee Weekly Hour Limits Constraint (HARD)")
        print(f"     No Scheme P employees found\n")
        return
    
    # Group slots by (emp_id, week_key, date)
    emp_week_slots = defaultdict(list)  # (emp_id, week_key) -> [slots]
    emp_week_dates = defaultdict(set)   # (emp_id, week_key) -> {dates}
    
    for slot in slots:
        # slot.date is already a date object, no need to convert
        slot_date = slot.date
        iso_year, iso_week, _ = slot_date.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"
        
        for emp_id in scheme_p_employees:
            if (slot.slot_id, emp_id) in x:
                emp_week_slots[(emp_id, week_key)].append(slot)
                # Store date as string for dictionary key
                date_str = slot_date.isoformat()
                emp_week_dates[(emp_id, week_key)].add(date_str)
    
    # Add constraints for each Scheme P employee per week
    constraints_added = 0
    max_hours_4days = 34.98   # If working ≤4 days
    max_hours_more = 29.98    # If working >4 days
    
    for (emp_id, week_key), week_slots in emp_week_slots.items():
        dates_in_week = emp_week_dates[(emp_id, week_key)]
        
        # Create day-worked indicator variables for this week
        day_worked = {}
        for date_str in dates_in_week:
            day_var = model.NewBoolVar(f'day_worked_c6_{emp_id}_{date_str}')
            day_worked[date_str] = day_var
            
            # Link day_var to slot assignments on this date
            # Compare using isoformat() since date_str is now a string
            date_slots = [s for s in week_slots if s.date.isoformat() == date_str]
            date_slot_vars = [x[(s.slot_id, emp_id)] for s in date_slots if (s.slot_id, emp_id) in x]
            
            if date_slot_vars:
                # CRITICAL FIX: Bidirectional linking between day_var and slot assignments
                # If ANY slot is assigned on this date → day_var MUST be 1
                # If day_var is 1 → at least one slot MUST be assigned
                
                # Forward: If any slot assigned, day_var must be 1
                # This is equivalent to: day_var >= max(slot_vars)
                for slot_var in date_slot_vars:
                    model.Add(day_var >= slot_var)
                
                # Backward: If day_var = 1, then sum of slots >= 1
                # If day_var = 0, then sum of slots = 0
                # This enforces: day_var = 1 iff at least one slot is assigned
                model.Add(sum(date_slot_vars) >= day_var)
                model.Add(sum(date_slot_vars) == 0).OnlyEnforceIf(day_var.Not())
        
        # Count working days in this week
        num_working_days_var = sum(day_worked.values())
        
        # Calculate total hours for this week
        hour_terms = []
        for slot in week_slots:
            if (slot.slot_id, emp_id) in x:
                var = x[(slot.slot_id, emp_id)]
                gross_hours = (slot.end - slot.start).total_seconds() / 3600.0
                
                if gross_hours > 0:
                    # Scale to integer tenths (×10)
                    int_hours = int(round(gross_hours * 10))
                    hour_terms.append(var * int_hours)
        
        if not hour_terms:
            continue
        
        total_hours_var = sum(hour_terms)
        
        # Constraint approach: Use two inequalities with indicator variables
        # Create boolean: is_4days_or_less = (working_days <= 4)
        is_4days_or_less = model.NewBoolVar(f'is_4days_{emp_id}_{week_key}')
        
        # Link is_4days_or_less to num_working_days
        # is_4days_or_less = 1 iff num_working_days <= 4
        model.Add(num_working_days_var <= 4).OnlyEnforceIf(is_4days_or_less)
        model.Add(num_working_days_var >= 5).OnlyEnforceIf(is_4days_or_less.Not())
        
        # Apply appropriate hour limit based on working days
        max_hours_4days_scaled = int(round(max_hours_4days * 10))  # 349.8 → 350
        max_hours_more_scaled = int(round(max_hours_more * 10))    # 299.8 → 300
        
        # If working ≤4 days: hours ≤ 34.98
        model.Add(total_hours_var <= max_hours_4days_scaled).OnlyEnforceIf(is_4days_or_less)
        
        # If working >4 days: hours ≤ 29.98
        model.Add(total_hours_var <= max_hours_more_scaled).OnlyEnforceIf(is_4days_or_less.Not())
        
        constraints_added += 1
    
    print(f"[C6] Part-Time Employee Weekly Hour Limits Constraint (HARD)")
    print(f"     Total employees: {len(employees)}")
    print(f"     Scheme P (part-time) employees: {len(scheme_p_employees)}")
    print(f"     Limits: ≤{max_hours_4days}h (≤4 days), ≤{max_hours_more}h (>4 days)")
    print(f"     ✓ Added {constraints_added} conditional hour limit constraints\n")
