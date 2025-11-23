"""Test suite for time_utils working hours calculation."""

from datetime import datetime
from context.engine.time_utils import (
    span_hours,
    lunch_hours,
    split_normal_ot,
    split_shift_hours,
    calculate_weekly_normal_hours,
    calculate_monthly_ot_hours,
    calculate_daily_gross_hours
)


def test_span_hours():
    """Test basic hour calculation."""
    # 09:00-18:00 = 9 hours
    dt1 = datetime(2025, 1, 1, 9, 0)
    dt2 = datetime(2025, 1, 1, 18, 0)
    assert span_hours(dt1, dt2) == 9.0, "9-to-6 should be 9 hours"
    
    # 09:00-20:00 = 11 hours
    dt3 = datetime(2025, 1, 1, 9, 0)
    dt4 = datetime(2025, 1, 1, 20, 0)
    assert span_hours(dt3, dt4) == 11.0, "9 to 8pm should be 11 hours"
    
    # Overnight: 22:00-06:00 (next day) = 8 hours
    dt5 = datetime(2025, 1, 1, 22, 0)
    dt6 = datetime(2025, 1, 2, 6, 0)
    assert span_hours(dt5, dt6) == 8.0, "10pm to 6am should be 8 hours"
    
    print("✓ span_hours tests passed")


def test_lunch_hours():
    """Test lunch break logic."""
    assert lunch_hours(4.0) == 0.0, "4h shift has no lunch"
    assert lunch_hours(6.0) == 0.0, "6h shift has no lunch (not > 6)"
    assert lunch_hours(6.1) == 1.0, "6.1h shift has 1h lunch"
    assert lunch_hours(9.0) == 1.0, "9h shift has 1h lunch"
    assert lunch_hours(11.0) == 1.0, "11h shift has 1h lunch (only one lunch per shift)"
    
    print("✓ lunch_hours tests passed")


def test_split_normal_ot():
    """Test normal vs OT splitting."""
    # 4h shift: no lunch, all normal
    n, ot = split_normal_ot(4.0)
    assert n == 4.0 and ot == 0.0, "4h should be all normal"
    
    # 8h shift: 1h lunch, 7h normal
    n, ot = split_normal_ot(8.0)
    assert n == 7.0 and ot == 0.0, "8h = 7h normal + 1h lunch"
    
    # 9h shift: 1h lunch, 8h normal
    n, ot = split_normal_ot(9.0)
    assert n == 8.0 and ot == 0.0, "9h = 8h normal + 1h lunch"
    
    # 11h shift: 1h lunch, 8h normal, 2h OT
    n, ot = split_normal_ot(11.0)
    assert n == 8.0 and ot == 2.0, "11h = 8h normal + 1h lunch + 2h OT"
    
    # 12h shift: 1h lunch, 8h normal, 3h OT
    n, ot = split_normal_ot(12.0)
    assert n == 8.0 and ot == 3.0, "12h = 8h normal + 1h lunch + 3h OT"
    
    print("✓ split_normal_ot tests passed")


def test_split_shift_hours():
    """Test complete shift breakdown."""
    # 09:00-18:00 = 9h shift
    dt1 = datetime(2025, 1, 1, 9, 0)
    dt2 = datetime(2025, 1, 1, 18, 0)
    result = split_shift_hours(dt1, dt2)
    assert result['gross'] == 9.0, "gross should be 9"
    assert result['lunch'] == 1.0, "lunch should be 1"
    assert result['normal'] == 8.0, "normal should be 8"
    assert result['ot'] == 0.0, "ot should be 0"
    assert result['paid'] == 9.0, "paid should be 9"
    print("  Sample: 09:00-18:00 →", result)
    
    # 09:00-20:00 = 11h shift
    dt3 = datetime(2025, 1, 1, 9, 0)
    dt4 = datetime(2025, 1, 1, 20, 0)
    result = split_shift_hours(dt3, dt4)
    assert result['gross'] == 11.0, "gross should be 11"
    assert result['lunch'] == 1.0, "lunch should be 1"
    assert result['normal'] == 8.0, "normal should be 8"
    assert result['ot'] == 2.0, "ot should be 2"
    print("  Sample: 09:00-20:00 →", result)
    
    # 19:00-23:30 = 4.5h short evening shift
    dt5 = datetime(2025, 1, 1, 19, 0)
    dt6 = datetime(2025, 1, 1, 23, 30)
    result = split_shift_hours(dt5, dt6)
    assert result['gross'] == 4.5, "gross should be 4.5"
    assert result['lunch'] == 0.0, "lunch should be 0 (< 6h)"
    assert result['normal'] == 4.5, "normal should be 4.5"
    assert result['ot'] == 0.0, "ot should be 0"
    print("  Sample: 19:00-23:30 →", result)
    
    print("✓ split_shift_hours tests passed")


def test_weekly_and_monthly_totals():
    """Test weekly normal hours and monthly OT calculations."""
    # Create shifts: 3 shifts of 9h each (8h normal, 1h lunch each)
    shifts = [
        (datetime(2025, 1, 1, 9, 0), datetime(2025, 1, 1, 18, 0)),   # 9h
        (datetime(2025, 1, 2, 9, 0), datetime(2025, 1, 2, 18, 0)),   # 9h
        (datetime(2025, 1, 3, 9, 0), datetime(2025, 1, 3, 18, 0)),   # 9h
    ]
    
    weekly_normal = calculate_weekly_normal_hours(shifts)
    assert weekly_normal == 24.0, f"3 × 9h shifts should be 24h normal, got {weekly_normal}"
    print(f"  Weekly normal: 3×9h shifts = {weekly_normal}h")
    
    # Add 2 OT shifts: 11h each (8h normal, 1h lunch, 2h OT)
    shifts_with_ot = [
        (datetime(2025, 1, 4, 9, 0), datetime(2025, 1, 4, 20, 0)),   # 11h = 8n + 1l + 2ot
        (datetime(2025, 1, 5, 9, 0), datetime(2025, 1, 5, 20, 0)),   # 11h = 8n + 1l + 2ot
    ]
    
    monthly_ot = calculate_monthly_ot_hours(shifts_with_ot)
    assert monthly_ot == 4.0, f"2 × 11h shifts should be 4h OT, got {monthly_ot}"
    print(f"  Monthly OT: 2×11h shifts = {monthly_ot}h")
    
    print("✓ weekly and monthly totals tests passed")


def test_daily_gross_hours():
    """Test daily gross hours for multiple shifts in a day."""
    # Two shifts on same day: 6h + 4h = 10h gross
    shifts_same_day = [
        (datetime(2025, 1, 1, 9, 0), datetime(2025, 1, 1, 15, 0)),   # 6h
        (datetime(2025, 1, 1, 16, 0), datetime(2025, 1, 1, 20, 0)),  # 4h
    ]
    
    daily_gross = calculate_daily_gross_hours(shifts_same_day)
    assert daily_gross == 10.0, f"6h + 4h should be 10h gross, got {daily_gross}"
    print(f"  Daily gross: 6h + 4h = {daily_gross}h")
    
    print("✓ daily gross hours tests passed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("Testing time_utils.py - Working Hours Calculation")
    print("="*60 + "\n")
    
    test_span_hours()
    test_lunch_hours()
    test_split_normal_ot()
    test_split_shift_hours()
    test_weekly_and_monthly_totals()
    test_daily_gross_hours()
    
    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60 + "\n")


if __name__ == '__main__':
    run_all_tests()
