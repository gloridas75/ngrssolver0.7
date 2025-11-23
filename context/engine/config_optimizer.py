#!/usr/bin/env python3
"""Configuration Optimizer - Find optimal work patterns and employee counts.

This module optimizes roster configuration by finding the best:
1. Work patterns for each requirement
2. Minimum employee count needed
3. Rotation offsets for employees
"""

from datetime import datetime
from typing import List, Dict, Tuple
from itertools import product
from .coverage_simulator import (
    simulate_coverage,
    calculate_min_employees,
    verify_pattern_feasibility,
    generate_staggered_offsets,
    evaluate_coverage_quality
)


def generate_pattern_candidates(
    shift_types: List[str],
    cycle_length: int = 6,
    min_work_days: int = 3,
    max_work_days: int = 5
) -> List[List[str]]:
    """
    Generate candidate work patterns.
    
    Args:
        shift_types: Available shift types (e.g., ['D', 'N'])
        cycle_length: Length of rotation cycle
        min_work_days: Minimum work days in cycle
        max_work_days: Maximum work days in cycle
    
    Returns:
        List of candidate patterns
    """
    candidates = []
    
    # Single shift type patterns
    for shift in shift_types:
        for work_days in range(min_work_days, max_work_days + 1):
            off_days = cycle_length - work_days
            
            # Consecutive work days pattern
            pattern = [shift] * work_days + ['O'] * off_days
            candidates.append(pattern)
            
            # Distributed pattern (if possible)
            if work_days >= 2 and off_days >= 2:
                # Split work days: first half, off, second half, off
                first_half = work_days // 2
                second_half = work_days - first_half
                first_off = off_days // 2
                second_off = off_days - first_off
                
                pattern = [shift] * first_half + ['O'] * first_off + [shift] * second_half + ['O'] * second_off
                if len(pattern) == cycle_length:
                    candidates.append(pattern)
    
    # Mixed shift patterns (for requirements with multiple shift types)
    if len(shift_types) >= 2:
        for work_days in range(min_work_days, max_work_days + 1):
            off_days = cycle_length - work_days
            
            # Split work days between shift types
            for split in range(1, work_days):
                pattern = [shift_types[0]] * split + [shift_types[1]] * (work_days - split) + ['O'] * off_days
                if len(pattern) == cycle_length:
                    candidates.append(pattern)
    
    # Remove duplicates
    unique_patterns = []
    seen = set()
    for pattern in candidates:
        pattern_tuple = tuple(pattern)
        if pattern_tuple not in seen:
            seen.add(pattern_tuple)
            unique_patterns.append(pattern)
    
    return unique_patterns


def optimize_requirement_config(
    requirement: Dict,
    constraints: Dict,
    days_in_horizon: int,
    anchor_date: datetime
) -> Dict:
    """
    Find optimal configuration for a single requirement.
    
    Args:
        requirement: Requirement specification
        constraints: Constraint parameters
        days_in_horizon: Planning horizon length
        anchor_date: Coverage anchor date
    
    Returns:
        Optimal configuration with pattern, employee count, offsets
    """
    shift_types = requirement['shiftTypes']
    headcount = requirement['headcountPerDay']
    
    # Generate candidate patterns
    candidates = generate_pattern_candidates(
        shift_types=shift_types,
        cycle_length=6,  # Standard 6-day cycle
        min_work_days=3,
        max_work_days=5
    )
    
    print(f"  Generated {len(candidates)} candidate patterns for {requirement['id']}")
    
    # Evaluate each candidate
    best_config = None
    best_score = float('inf')
    
    shift_normal_hours = 11.0  # 12 gross - 1 lunch
    max_weekly_hours = constraints.get('maxWeeklyNormalHours', 44)
    
    for pattern in candidates:
        # Check feasibility
        is_feasible, issues = verify_pattern_feasibility(pattern, constraints)
        if not is_feasible:
            continue
        
        # Calculate minimum employees needed
        min_employees = calculate_min_employees(
            pattern,
            headcount,
            days_in_horizon,
            max_weekly_hours,
            shift_normal_hours
        )
        
        # Generate staggered offsets
        offsets = generate_staggered_offsets(min_employees, len(pattern))
        
        # Simulate coverage
        coverage = simulate_coverage(
            pattern,
            min_employees,
            offsets,
            headcount,
            days_in_horizon,
            anchor_date
        )
        
        # Evaluate quality
        quality = evaluate_coverage_quality(
            coverage['coverageMap'],
            headcount
        )
        
        # Score: prioritize fewer employees + high coverage + balance
        # Lower score is better
        coverage_penalty = (100 - coverage['coverageRate']) * 100  # Heavy penalty for low coverage
        employee_penalty = min_employees * 10  # Prefer fewer employees
        balance_penalty = quality['variance']  # Prefer balanced coverage
        
        score = coverage_penalty + employee_penalty + balance_penalty
        
        if score < best_score:
            best_score = score
            best_config = {
                'pattern': pattern,
                'employeeCount': min_employees,
                'offsets': offsets,
                'coverage': coverage,
                'quality': quality,
                'score': round(score, 2)
            }
    
    return best_config


def optimize_all_requirements(
    requirements: List[Dict],
    constraints: Dict,
    planning_horizon: Dict
) -> Dict:
    """
    Optimize configuration for all requirements.
    
    Args:
        requirements: List of requirement specifications
        constraints: Constraint parameters
        planning_horizon: Planning horizon with start/end dates
    
    Returns:
        Optimal configuration for all requirements
    """
    start_date = datetime.fromisoformat(planning_horizon['startDate'])
    end_date = datetime.fromisoformat(planning_horizon['endDate'])
    days_in_horizon = (end_date - start_date).days + 1
    
    print(f"\n{'='*80}")
    print(f"OPTIMIZING CONFIGURATION FOR {len(requirements)} REQUIREMENTS")
    print(f"{'='*80}\n")
    print(f"Planning horizon: {start_date.date()} to {end_date.date()} ({days_in_horizon} days)\n")
    
    optimized_configs = {}
    total_employees = 0
    
    for req in requirements:
        print(f"Optimizing: {req['id']} ({req['name']})")
        print(f"  Shift types: {req['shiftTypes']}, Headcount: {req['headcountPerDay']}")
        
        config = optimize_requirement_config(
            req,
            constraints,
            days_in_horizon,
            start_date
        )
        
        if config:
            optimized_configs[req['id']] = config
            total_employees += config['employeeCount']
            
            print(f"  ✓ Optimal pattern: {config['pattern']}")
            print(f"  ✓ Employees needed: {config['employeeCount']}")
            print(f"  ✓ Coverage rate: {config['coverage']['coverageRate']:.1f}%")
            print(f"  ✓ Balance score: {config['quality']['balanceScore']:.1f}")
            print()
        else:
            print(f"  ✗ No feasible configuration found!")
            print()
    
    print(f"{'='*80}")
    print(f"OPTIMIZATION COMPLETE")
    print(f"{'='*80}")
    print(f"Total requirements: {len(requirements)}")
    print(f"Total employees needed: {total_employees}")
    print(f"{'='*80}\n")
    
    return {
        'requirements': optimized_configs,
        'summary': {
            'totalRequirements': len(requirements),
            'totalEmployees': total_employees,
            'planningHorizon': {
                'startDate': start_date.isoformat(),
                'endDate': end_date.isoformat(),
                'days': days_in_horizon
            }
        }
    }


def format_output_config(optimized_result: Dict, requirements: List[Dict]) -> Dict:
    """
    Format optimized result for output JSON.
    
    Args:
        optimized_result: Result from optimize_all_requirements
        requirements: Original requirement specifications
    
    Returns:
        Formatted configuration for output
    """
    req_map = {req['id']: req for req in requirements}
    
    formatted = {
        'schemaVersion': '0.8',
        'configType': 'optimizedRosterConfiguration',
        'generatedAt': datetime.now().isoformat(),
        'summary': optimized_result['summary'],
        'recommendations': []
    }
    
    for req_id, config in optimized_result['requirements'].items():
        req = req_map.get(req_id, {})
        
        recommendation = {
            'requirementId': req_id,
            'requirementName': req.get('name', ''),
            'productType': req.get('productType', ''),
            'rank': req.get('rank', ''),
            'scheme': req.get('scheme', ''),
            'configuration': {
                'workPattern': config['pattern'],
                'employeesRequired': config['employeeCount'],
                'rotationOffsets': config['offsets'],
                'cycleLength': len(config['pattern'])
            },
            'coverage': {
                'expectedCoverageRate': round(config['coverage']['coverageRate'], 2),
                'daysFullyCovered': config['coverage']['daysFullyCovered'],
                'daysUndercovered': config['coverage']['daysUndercovered'],
                'averageAvailable': config['coverage']['averageAvailable'],
                'requiredPerDay': config['coverage']['requiredPerDay']
            },
            'quality': {
                'balanceScore': config['quality']['balanceScore'],
                'variance': config['quality']['variance'],
                'totalExcessCoverage': config['quality']['totalExcessCoverage']
            },
            'notes': _generate_notes(config, req)
        }
        
        formatted['recommendations'].append(recommendation)
    
    return formatted


def _generate_notes(config: Dict, requirement: Dict) -> List[str]:
    """Generate helpful notes about the configuration."""
    notes = []
    
    pattern = config['pattern']
    work_days = sum(1 for d in pattern if d != 'O')
    off_days = len(pattern) - work_days
    
    notes.append(f"Pattern has {work_days} work days and {off_days} off days per {len(pattern)}-day cycle")
    
    if config['coverage']['coverageRate'] == 100:
        notes.append("✓ Achieves 100% coverage with this configuration")
    elif config['coverage']['coverageRate'] >= 95:
        notes.append(f"Achieves {config['coverage']['coverageRate']:.1f}% coverage (near-optimal)")
    else:
        notes.append(f"Warning: Only {config['coverage']['coverageRate']:.1f}% coverage - may need more employees")
    
    if config['quality']['variance'] < 1.0:
        notes.append("✓ Excellent workload balance across employees")
    elif config['quality']['variance'] < 2.0:
        notes.append("Good workload balance")
    
    offsets = config['offsets']
    if len(set(offsets)) == len(offsets):
        notes.append("✓ All employees have unique rotation offsets for maximum diversity")
    
    return notes
