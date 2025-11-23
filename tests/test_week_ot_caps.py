"""Test suite for C2 (weekly 44h cap) and C17 (monthly 72h OT cap).

Test cases:
  1. 5×9h baseline (PASS weekly)
     Mon–Fri, 09:00–18:00 → weekly normal = 5×8 = 40h ✓
  
  2. 6×9h (FAIL weekly)
     Mon–Sat, 09:00–18:00 → weekly normal = 6×8 = 48h ✗ (exceeds 44h)
  
  3. 11×7 with OT
     Mon–Sun, 09:00–20:00 → daily (normal=8, OT=2).
     Weekly normal = 7×8 = 56h ✗ (exceeds 44h)
     Monthly OT accumulates (2×days) toward 72h cap
  
  4. Monthly OT boundary
     12 days with 11h shifts → OT = 24h ✓
     36 days with 11h shifts → OT = 72h ✓
     37 days with 11h shifts → OT = 74h ✗ (exceeds 72h monthly)
"""

from datetime import datetime, timedelta
from context.engine.time_utils import split_shift_hours, calculate_weekly_normal_hours, calculate_monthly_ot_hours


def test_5x9h_baseline_pass_weekly():
    """Test case: 5×9h week (Mon–Fri 09:00–18:00).
    
    Expected:
    - Each day: gross=9, lunch=1, normal=8, ot=0
    - Weekly total: normal = 5×8 = 40h
    - Status: ✓ PASS (40h ≤ 44h weekly cap)
    """
    print("\n" + "="*70)
    print("TEST 1: 5×9h baseline (Mon–Fri 09:00–18:00)")
    print("="*70)
    
    shifts = []
    for day in range(5):  # Mon-Fri = 5 days
        start = datetime(2025, 11, 3, 9, 0) + timedelta(days=day)
        end = datetime(2025, 11, 3, 18, 0) + timedelta(days=day)
        shifts.append((start, end))
    
    # Calculate totals
    weekly_normal = calculate_weekly_normal_hours(shifts)
    
    print(f"Shifts: 5 days × 9h (09:00-18:00)")
    print(f"Expected normal per day: 8h (9h - 1h lunch)")
    print(f"Expected weekly normal: 5×8 = 40h")
    print(f"Actual weekly normal: {weekly_normal}h")
    
    # Verify
    assert weekly_normal == 40.0, f"Expected 40h, got {weekly_normal}h"
    assert weekly_normal <= 44.0, f"Weekly normal {weekly_normal}h exceeds 44h cap"
    
    print(f"✅ PASS: {weekly_normal}h ≤ 44h weekly cap")
    return True


def test_6x9h_fail_weekly():
    """Test case: 6×9h week (Mon–Sat 09:00–18:00).
    
    Expected:
    - Each day: gross=9, lunch=1, normal=8, ot=0
    - Weekly total: normal = 6×8 = 48h
    - Status: ✗ FAIL (48h > 44h weekly cap) — C2 violation
    """
    print("\n" + "="*70)
    print("TEST 2: 6×9h (Mon–Sat 09:00–18:00) — SHOULD FAIL")
    print("="*70)
    
    shifts = []
    for day in range(6):  # Mon-Sat = 6 days
        start = datetime(2025, 11, 3, 9, 0) + timedelta(days=day)
        end = datetime(2025, 11, 3, 18, 0) + timedelta(days=day)
        shifts.append((start, end))
    
    # Calculate totals
    weekly_normal = calculate_weekly_normal_hours(shifts)
    
    print(f"Shifts: 6 days × 9h (09:00-18:00)")
    print(f"Expected normal per day: 8h (9h - 1h lunch)")
    print(f"Expected weekly normal: 6×8 = 48h")
    print(f"Actual weekly normal: {weekly_normal}h")
    
    # Verify violation
    assert weekly_normal == 48.0, f"Expected 48h, got {weekly_normal}h"
    assert weekly_normal > 44.0, f"Weekly normal {weekly_normal}h should exceed 44h cap"
    
    print(f"❌ VIOLATION (C2): {weekly_normal}h > 44h weekly cap")
    return True


def test_7x11h_fail_weekly_and_ot():
    """Test case: 7×11h week (Mon–Sun 09:00–20:00).
    
    Expected:
    - Each day: gross=11, lunch=1, normal=8, ot=2
    - Weekly normal: 7×8 = 56h (✗ exceeds 44h cap)
    - Weekly OT: 7×2 = 14h
    - Monthly OT: 14h (below 72h cap)
    - Status: ✗ FAIL weekly (C2 violation), but OK for OT
    """
    print("\n" + "="*70)
    print("TEST 3: 7×11h (Mon–Sun 09:00–20:00) — SHOULD FAIL WEEKLY")
    print("="*70)
    
    shifts = []
    for day in range(7):  # Mon-Sun = 7 days
        start = datetime(2025, 11, 3, 9, 0) + timedelta(days=day)
        end = datetime(2025, 11, 3, 20, 0) + timedelta(days=day)
        shifts.append((start, end))
    
    # Calculate totals
    weekly_normal = calculate_weekly_normal_hours(shifts)
    monthly_ot = calculate_monthly_ot_hours(shifts)
    
    print(f"Shifts: 7 days × 11h (09:00-20:00)")
    print(f"Expected per day: gross=11, lunch=1, normal=8, ot=2")
    print(f"Expected weekly normal: 7×8 = 56h")
    print(f"Expected weekly OT: 7×2 = 14h")
    print(f"Expected monthly OT: 14h")
    print(f"")
    print(f"Actual weekly normal: {weekly_normal}h")
    print(f"Actual monthly OT: {monthly_ot}h")
    
    # Verify violations
    assert weekly_normal == 56.0, f"Expected normal 56h, got {weekly_normal}h"
    assert weekly_normal > 44.0, f"Weekly normal {weekly_normal}h should exceed 44h cap"
    assert monthly_ot == 14.0, f"Expected OT 14h, got {monthly_ot}h"
    assert monthly_ot <= 72.0, f"Monthly OT {monthly_ot}h should not exceed 72h cap"
    
    print(f"❌ VIOLATION (C2): Weekly normal {weekly_normal}h > 44h")
    print(f"✅ OK (C17): Monthly OT {monthly_ot}h ≤ 72h")
    return True


def test_12_days_11h_monthly_ot_pass():
    """Test case: 12 days with 11h shifts in one month.
    
    Expected:
    - Each shift: ot=2h (gross=11 → min(11,9)-1 + (11-9) = 8+2)
    - Monthly OT: 12×2 = 24h
    - Status: ✓ PASS (24h ≤ 72h monthly cap)
    """
    print("\n" + "="*70)
    print("TEST 4: 12 days × 11h shifts — MONTHLY OT PASS")
    print("="*70)
    
    shifts = []
    for day in range(12):
        start = datetime(2025, 11, 1, 9, 0) + timedelta(days=day)
        end = datetime(2025, 11, 1, 20, 0) + timedelta(days=day)
        shifts.append((start, end))
    
    # Calculate totals
    monthly_ot = calculate_monthly_ot_hours(shifts)
    
    print(f"Shifts: 12 days × 11h (09:00-20:00)")
    print(f"Expected OT per day: 2h (11h - 9h cap)")
    print(f"Expected monthly OT: 12×2 = 24h")
    print(f"Actual monthly OT: {monthly_ot}h")
    
    # Verify
    assert monthly_ot == 24.0, f"Expected OT 24h, got {monthly_ot}h"
    assert monthly_ot <= 72.0, f"Monthly OT {monthly_ot}h exceeds 72h cap"
    
    print(f"✅ PASS: Monthly OT {monthly_ot}h ≤ 72h monthly cap")
    return True


def test_36_days_11h_monthly_ot_boundary():
    """Test case: 36 days with 11h shifts in one month (boundary).
    
    Expected:
    - Each shift: ot=2h
    - Monthly OT: 36×2 = 72h
    - Status: ✓ PASS (72h = 72h monthly cap, exactly at boundary)
    """
    print("\n" + "="*70)
    print("TEST 5: 36 days × 11h shifts — MONTHLY OT AT BOUNDARY")
    print("="*70)
    
    shifts = []
    # Note: November has 30 days, so we'll create 36 shifts (spanning into Dec if needed)
    for day in range(36):
        start = datetime(2025, 11, 1, 9, 0) + timedelta(days=day)
        end = datetime(2025, 11, 1, 20, 0) + timedelta(days=day)
        shifts.append((start, end))
    
    # Calculate totals
    monthly_ot = calculate_monthly_ot_hours(shifts)
    
    print(f"Shifts: 36 days × 11h (09:00-20:00)")
    print(f"Expected OT per day: 2h")
    print(f"Expected total OT: 36×2 = 72h")
    print(f"Actual total OT: {monthly_ot}h")
    
    # Verify
    assert monthly_ot == 72.0, f"Expected OT 72h, got {monthly_ot}h"
    assert monthly_ot <= 72.0, f"Monthly OT {monthly_ot}h at boundary (exactly 72h)"
    
    print(f"✅ BOUNDARY: Monthly OT {monthly_ot}h = 72h (at cap limit)")
    return True


def test_37_days_11h_monthly_ot_exceed():
    """Test case: 37 days with 11h shifts (exceeds monthly OT cap).
    
    Expected:
    - Each shift: ot=2h
    - Monthly OT: 37×2 = 74h
    - Status: ✗ FAIL (74h > 72h monthly cap) — C17 violation
    """
    print("\n" + "="*70)
    print("TEST 6: 37 days × 11h shifts — MONTHLY OT EXCEED (SHOULD FAIL)")
    print("="*70)
    
    shifts = []
    for day in range(37):
        start = datetime(2025, 11, 1, 9, 0) + timedelta(days=day)
        end = datetime(2025, 11, 1, 20, 0) + timedelta(days=day)
        shifts.append((start, end))
    
    # Calculate totals
    monthly_ot = calculate_monthly_ot_hours(shifts)
    
    print(f"Shifts: 37 days × 11h (09:00-20:00)")
    print(f"Expected OT per day: 2h")
    print(f"Expected total OT: 37×2 = 74h")
    print(f"Actual total OT: {monthly_ot}h")
    
    # Verify violation
    assert monthly_ot == 74.0, f"Expected OT 74h, got {monthly_ot}h"
    assert monthly_ot > 72.0, f"Monthly OT {monthly_ot}h should exceed 72h cap"
    
    print(f"❌ VIOLATION (C17): Monthly OT {monthly_ot}h > 72h monthly cap")
    return True


def test_hour_breakdown_samples():
    """Show sample hour breakdowns for reference."""
    print("\n" + "="*70)
    print("REFERENCE: Hour Breakdown Examples")
    print("="*70)
    
    test_cases = [
        ("9h day shift", datetime(2025, 11, 3, 9, 0), datetime(2025, 11, 3, 18, 0)),
        ("11h day shift (2h OT)", datetime(2025, 11, 3, 9, 0), datetime(2025, 11, 3, 20, 0)),
        ("12h night shift (3h OT)", datetime(2025, 11, 3, 19, 0), datetime(2025, 11, 4, 7, 0)),
        ("4h short shift", datetime(2025, 11, 3, 14, 0), datetime(2025, 11, 3, 18, 0)),
    ]
    
    for label, start, end in test_cases:
        hours = split_shift_hours(start, end)
        print(f"\n{label}:")
        print(f"  Time: {start.strftime('%H:%M')} → {end.strftime('%H:%M')}")
        print(f"  Breakdown: gross={hours['gross']}h, lunch={hours['lunch']}h, "
              f"normal={hours['normal']}h, ot={hours['ot']}h")


def run_all_tests():
    """Run all test cases."""
    print("\n" + "="*70)
    print("NGRS SOLVER: Weekly (C2) & Monthly OT (C17) CAP TESTS")
    print("="*70)
    
    results = []
    
    try:
        results.append(("5×9h baseline (PASS weekly)", test_5x9h_baseline_pass_weekly()))
    except AssertionError as e:
        results.append(("5×9h baseline (PASS weekly)", f"FAILED: {e}"))
    
    try:
        results.append(("6×9h (FAIL weekly)", test_6x9h_fail_weekly()))
    except AssertionError as e:
        results.append(("6×9h (FAIL weekly)", f"FAILED: {e}"))
    
    try:
        results.append(("7×11h (FAIL weekly, OT ok)", test_7x11h_fail_weekly_and_ot()))
    except AssertionError as e:
        results.append(("7×11h (FAIL weekly, OT ok)", f"FAILED: {e}"))
    
    try:
        results.append(("12 days 11h (PASS OT)", test_12_days_11h_monthly_ot_pass()))
    except AssertionError as e:
        results.append(("12 days 11h (PASS OT)", f"FAILED: {e}"))
    
    try:
        results.append(("36 days 11h (BOUNDARY OT)", test_36_days_11h_monthly_ot_boundary()))
    except AssertionError as e:
        results.append(("36 days 11h (BOUNDARY OT)", f"FAILED: {e}"))
    
    try:
        results.append(("37 days 11h (EXCEED OT)", test_37_days_11h_monthly_ot_exceed()))
    except AssertionError as e:
        results.append(("37 days 11h (EXCEED OT)", f"FAILED: {e}"))
    
    test_hour_breakdown_samples()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result is True)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result is True else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        return True
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
