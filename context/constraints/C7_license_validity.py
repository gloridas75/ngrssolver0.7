"""C7: License/qualification must be valid on shift date.

Enforce that employees can only be assigned to shifts requiring qualifications
they actually hold and that are currently valid (not expired).

Input Schema (v0.70):
- employees: [{ employeeId, licenses: [{ code, expiryDate }], ... }]
- Slot objects have requiredQualifications from requirements
- planningHorizon: { startDate, endDate }
"""
from datetime import datetime


def add_constraints(model, ctx):
    """
    Enforce that employees have valid licenses/qualifications for assigned shifts (HARD).
    
    This constraint ensures that:
    1. Employee has the required qualification in their credentials
    2. The qualification has not expired on the shift date
    
    Args:
        model: CP-SAT model from ortools
        ctx: Context dict with planning data
    """
    
    employees = ctx.get('employees', [])
    slots = ctx.get('slots', [])
    x = ctx.get('x', {})
    
    if not slots or not x:
        print(f"[C7] Warning: Slots or decision variables not available")
        return
    
    # Build employee license map: emp_id -> {license_code -> expiry_date}
    # v0.70: Check both 'licenses' and 'qualifications' fields for compatibility
    employee_licenses = {}
    for emp in employees:
        emp_id = emp.get('employeeId')
        licenses = {}
        
        # Check 'licenses' field (old schema)
        for lic in emp.get('licenses', []):
            code = lic.get('code')
            expiry = lic.get('expiryDate')
            if code and expiry:
                licenses[code] = expiry
        
        # Also check 'qualifications' field (v0.70 schema)
        for qual in emp.get('qualifications', []):
            code = qual.get('code')
            expiry = qual.get('expiryDate')
            if code and expiry:
                licenses[code] = expiry
        
        employee_licenses[emp_id] = licenses
    
    # Add constraints: for each slot-employee pair, verify qualifications
    # v0.70: requiredQualifications is directly on slot from requirement
    license_constraints = 0
    for slot in slots:
        slot_date = slot.date  # This is a date object from Slot dataclass
        required_quals = set(getattr(slot, 'requiredQualifications', []))
        
        # Skip if no qualifications required for this slot
        if not required_quals:
            continue
        
        for emp in employees:
            emp_id = emp.get('employeeId')
            emp_licenses = employee_licenses.get(emp_id, {})
            
            if (slot.slot_id, emp_id) not in x:
                continue
            
            # Check if employee has all required qualifications and they're not expired
            has_valid_quals = True
            for qual_code in required_quals:
                if qual_code not in emp_licenses:
                    # Employee doesn't have this qualification
                    has_valid_quals = False
                    break
                
                expiry_date_str = emp_licenses[qual_code]
                try:
                    expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                    # Qualification is invalid if shift date is after expiry date
                    # (expiry date is the last valid day)
                    if slot_date > expiry_date:
                        # Qualification has expired
                        has_valid_quals = False
                        break
                except (ValueError, AttributeError):
                    # Failed to parse expiry date - treat as invalid
                    has_valid_quals = False
                    break
            
            # If employee doesn't have valid qualifications, block assignment
            if not has_valid_quals:
                var = x[(slot.slot_id, emp_id)]
                # Add constraint: var must be 0 (not assigned)
                model.Add(var == 0)
                license_constraints += 1
    
    # Collect statistics
    employees_with_licenses = sum(1 for emp in employees if (emp.get('licenses', []) or emp.get('qualifications', [])))
    slots_with_quals = sum(1 for s in slots if getattr(s, 'requiredQualifications', []))
    
    print(f"[C7] License Validity Constraint (HARD)")
    print(f"     Employees: {len(employees)} ({employees_with_licenses} have licenses)")
    print(f"     Slots: {len(slots)} ({slots_with_quals} require qualifications)")
    print(f"     ✓ Added {license_constraints} license validity constraints\n")
