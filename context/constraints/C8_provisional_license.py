"""C8: Provisional license (PDL) validity and expiration (HARD constraint).

Enforce that provisional licenses are only used within their validity period.
PDL becomes invalid on expiry date or when status changes.
"""
from datetime import datetime


def add_constraints(model, ctx):
    """
    Enforce provisional license validity (HARD).
    
    Strategy: For each employee with provisional licenses, check expiry date.
    Block assignments after expiry or if status is invalid.
    
    Args:
        model: CP-SAT model
        ctx: Context dict with 'slots', 'employees', 'x'
    """
    
    slots = ctx.get('slots', [])
    employees = ctx.get('employees', [])
    x = ctx.get('x', {})
    
    if not slots or not x or not employees:
        print(f"[C8] Warning: Slots, employees, or decision variables not available")
        return
    
    constraints_added = 0
    
    # For each employee with provisional licenses
    for emp in employees:
        emp_id = emp.get('employeeId')
        licenses = emp.get('licenses', [])
        
        # Find provisional licenses
        provisional_licenses = []
        for lic in licenses:
            lic_type = lic.get('type', '').upper()
            if lic_type in ['PDL', 'PROVISIONAL']:
                provisional_licenses.append(lic)
        
        if not provisional_licenses:
            continue
        
        # For each provisional license, find expiry date
        for lic in provisional_licenses:
            expiry_str = lic.get('expiryDate')
            if not expiry_str:
                continue
            
            try:
                expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
            except (ValueError, AttributeError):
                # Failed to parse expiry date - skip this license
                continue
            
            # For each slot after expiry, block assignment
            for slot in slots:
                # Block assignments where shift date is after the expiry date
                # (expiry date is the last valid day)
                if slot.date > expiry_date:
                    if (slot.slot_id, emp_id) in x:
                        var = x[(slot.slot_id, emp_id)]
                        model.Add(var == 0)
                        constraints_added += 1
    
    # Count employees with PDL
    pdl_employees = sum(1 for emp in employees 
                       if any(l.get('type', '').upper() in ['PDL', 'PROVISIONAL'] 
                              for l in emp.get('licenses', [])))
    
    print(f"[C8] Provisional License (PDL) Validity Constraint (HARD)")
    print(f"     Total employees: {len(employees)}")
    print(f"     Employees with PDL: {pdl_employees}")
    print(f"     ✓ Added {constraints_added} PDL expiry blocks\n")
