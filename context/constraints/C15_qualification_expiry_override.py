"""C15: Block expired qualifications unless temporary approval exists (HARD).

Stricter than C7: expired qualifications cannot be used even with documentation,
unless explicit temporary approval/extension is current and valid on the shift date.

Key difference from C7:
- C7: Checks if qualification exists and not expired
- C15: Blocks expired qualifications, allows only with valid approval override
"""

from datetime import datetime


def add_constraints(model, ctx):
    """
    Enforce qualification expiry with override controls (HARD).
    
    Strategy: For each slot requiring qualifications, check each employee:
    1. If qualification is expired AND no valid temporary approval → block
    2. If qualification is expired AND approval is also expired → block
    3. Otherwise allow (covered by C7)
    
    Args:
        model: CP-SAT model
        ctx: Context dict with 'slots', 'employees', 'x'
    """
    
    slots = ctx.get('slots', [])
    employees = ctx.get('employees', [])
    x = ctx.get('x', {})
    
    if not slots or not x or not employees:
        print(f"[C15] Qualification Expiry Override Control Constraint (HARD)")
        print(f"     Skipping: slots or decision variables not available\n")
        return
    
    # Build employee license+approval map
    emp_creds = {}
    for emp in employees:
        emp_id = emp.get('employeeId')
        creds = {}
        for lic in emp.get('licenses', []):
            code = lic.get('code')
            expiry = lic.get('expiryDate')
            approval = lic.get('approvalCode')
            approval_expiry = lic.get('temporaryApprovalExpiry')
            if code:
                creds[code] = {
                    'expiry': expiry,
                    'approval': approval,
                    'approval_expiry': approval_expiry
                }
        emp_creds[emp_id] = creds
    
    constraints_added = 0
    
    for slot in slots:
        slot_date = slot.date
        
        # Check if slot requires qualifications (look for required quals in demand)
        # If demand has shifts with requiredQualifications, those apply here
        # For now, assume any APO/AVSO product requires special quals
        required_quals = set()
        if slot.productTypeId in {'APO', 'AVSO'}:
            required_quals.add(slot.productTypeId)
        
        if not required_quals:
            continue
        
        for emp in employees:
            emp_id = emp.get('employeeId')
            
            if (slot.slot_id, emp_id) not in x:
                continue
            
            emp_creds_map = emp_creds.get(emp_id, {})
            
            # Check each required qualification
            has_valid_override = True
            for qual in required_quals:
                cred = emp_creds_map.get(qual, {})
                expiry_str = cred.get('expiry')
                approval_expiry_str = cred.get('approval_expiry')
                
                # Parse expiry date
                try:
                    expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date() if expiry_str else None
                except:
                    expiry_date = None
                
                # Check if qual is expired
                if expiry_date and slot_date > expiry_date:
                    # Qualification is expired; check for valid approval
                    try:
                        approval_exp = datetime.strptime(approval_expiry_str, '%Y-%m-%d').date() if approval_expiry_str else None
                    except:
                        approval_exp = None
                    
                    # If approval also expired or doesn't exist, cannot use
                    if not approval_exp or slot_date > approval_exp:
                        has_valid_override = False
                        break
            
            # If no valid override, block assignment
            if not has_valid_override:
                var = x[(slot.slot_id, emp_id)]
                model.Add(var == 0)
                constraints_added += 1
    
    print(f"[C15] Qualification Expiry Override Control Constraint (HARD)")
    print(f"     Employees: {len(employees)}, Slots: {len(slots)}")
    print(f"     ✓ Added {constraints_added} expiry override violation blocks\n")
