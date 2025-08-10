#!/usr/bin/env python3
"""
상세 분석 - 특정 시나리오에 대한 심화 분석
"""

import json
import glob
from collections import defaultdict
from datetime import datetime

def analyze_latest_schedules():
    """최근 생성된 스케줄들을 분석합니다."""
    
    # 최근 15개 스케줄 파일 찾기
    schedule_files = glob.glob("data/schedule_response_*.json")
    schedule_files.sort(reverse=True)
    recent_files = schedule_files[:15]
    
    print("🔍 최근 생성된 스케줄 상세 분석")
    print("=" * 60)
    
    scenarios = []
    
    for i, file_path in enumerate(recent_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data.get('protocol') != 'py_gen_schedule':
                continue
                
            schedule_data = data.get('data', [])
            if not schedule_data:
                continue
            
            # 기본 정보 수집
            dates = set()
            staff_info = {}
            staff_shifts = defaultdict(lambda: defaultdict(int))
            
            for entry in schedule_data:
                dates.add(entry['date'])
                shift = entry['shift']
                
                for person in entry['people']:
                    staff_id = person['staff_id']
                    staff_name = person['name']
                    staff_info[staff_id] = staff_name
                    staff_shifts[staff_id][shift] += 1
            
            # 형평성 계산
            off_days = [shifts['Off'] for shifts in staff_shifts.values()]
            if off_days:
                min_off = min(off_days)
                max_off = max(off_days)
                staff_count = len(staff_shifts)
                total_days = len(dates)
                
                # 교대 시스템 추정
                all_shifts = set()
                for entry in schedule_data:
                    all_shifts.add(entry['shift'])
                shift_type = len(all_shifts) - 1  # Off 제외
                
                scenarios.append({
                    'file': file_path.split('/')[-1],
                    'staff_count': staff_count,
                    'shift_type': shift_type,
                    'total_days': total_days,
                    'min_off': min_off,
                    'max_off': max_off,
                    'range': max_off - min_off,
                    'fairness_score': max(0, 100 - (max_off - min_off) * 20),
                    'staff_shifts': dict(staff_shifts),
                    'staff_info': staff_info
                })
        
        except Exception as e:
            continue
    
    # 시나리오별 분석
    print(f"📊 분석된 시나리오: {len(scenarios)}개")
    print()
    
    # 문제 시나리오 찾기
    problem_scenarios = [s for s in scenarios if s['fairness_score'] < 60]
    good_scenarios = [s for s in scenarios if s['fairness_score'] >= 80]
    
    print(f"🚨 문제 시나리오 ({len(problem_scenarios)}개):")
    for scenario in problem_scenarios[:3]:
        print(f"  • {scenario['staff_count']}명 {scenario['shift_type']}교대: 편차 {scenario['range']}일 (형평성 {scenario['fairness_score']:.1f}점)")
        analyze_scenario_details(scenario)
    
    print(f"\n✅ 우수 시나리오 ({len(good_scenarios)}개):")
    for scenario in good_scenarios[:3]:
        print(f"  • {scenario['staff_count']}명 {scenario['shift_type']}교대: 편차 {scenario['range']}일 (형평성 {scenario['fairness_score']:.1f}점)")
        analyze_scenario_details(scenario)

def analyze_scenario_details(scenario):
    """시나리오 상세 분석"""
    staff_shifts = scenario['staff_shifts']
    staff_info = scenario['staff_info']
    
    print(f"     파일: {scenario['file']}")
    print(f"     기간: {scenario['total_days']}일")
    
    # 휴무일 분포 분석
    off_distribution = {}
    for staff_id, shifts in staff_shifts.items():
        name = staff_info.get(staff_id, f'ID{staff_id}')
        off_days = shifts.get('Off', 0)
        off_distribution[name] = off_days
    
    # 상위/하위 3명
    sorted_off = sorted(off_distribution.items(), key=lambda x: x[1])
    
    print(f"     최소 휴무: {sorted_off[0][0]} ({sorted_off[0][1]}일)")
    print(f"     최대 휴무: {sorted_off[-1][0]} ({sorted_off[-1][1]}일)")
    
    # 교대별 근무 분포
    shift_totals = defaultdict(int)
    for shifts in staff_shifts.values():
        for shift, count in shifts.items():
            if shift != 'Off':
                shift_totals[shift] += count
    
    if shift_totals:
        print(f"     교대 분포: {dict(shift_totals)}")
    
    print()

if __name__ == "__main__":
    analyze_latest_schedules()