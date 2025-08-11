#!/usr/bin/env python3
"""
형평성 분석 스크립트 - 근무표에서 각 직원의 휴무일 분포를 분석합니다.
"""

import json
import glob
from collections import defaultdict
from typing import Dict, List, Tuple

def analyze_schedule_fairness(schedule_file: str) -> Dict[str, Dict[str, int]]:
    """근무표 파일을 분석하여 직원별 휴무일 및 근무일 수를 계산합니다."""
    
    with open(schedule_file, 'r', encoding='utf-8') as f:
        schedule_data = json.load(f)
    
    # 직원별 통계 초기화
    staff_stats = defaultdict(lambda: {
        'off_days': 0,
        'work_days': 0, 
        'total_hours': 0,
        'name': '',
        'shifts': defaultdict(int)
    })
    
    # 날짜별 데이터 파싱
    dates_processed = set()
    
    for entry in schedule_data.get('data', []):
        date = entry['date']
        shift = entry['shift']
        hours = entry['hours']
        people = entry['people']
        
        dates_processed.add(date)
        
        # 각 직원에 대해
        for person in people:
            staff_id = person['staff_id']
            name = person['name']
            
            staff_stats[staff_id]['name'] = name
            staff_stats[staff_id]['shifts'][shift] += 1
            staff_stats[staff_id]['total_hours'] += hours
            
            if shift == 'Off':
                staff_stats[staff_id]['off_days'] += 1
            else:
                staff_stats[staff_id]['work_days'] += 1
    
    total_days = len(dates_processed)
    
    print(f"📊 형평성 분석 결과")
    print(f"=" * 60)
    print(f"📅 분석 기간: {min(dates_processed)} ~ {max(dates_processed)}")
    print(f"📅 총 일수: {total_days}일")
    print(f"👥 직원 수: {len(staff_stats)}명")
    print()
    
    # 직원별 상세 분석
    for staff_id, stats in staff_stats.items():
        name = stats['name']
        off_days = stats['off_days']
        work_days = stats['work_days']
        total_hours = stats['total_hours']
        
        off_percentage = (off_days / total_days) * 100 if total_days > 0 else 0
        work_percentage = (work_days / total_days) * 100 if total_days > 0 else 0
        
        print(f"👤 {name} (ID: {staff_id})")
        print(f"   🏠 휴무일: {off_days}일 ({off_percentage:.1f}%)")
        print(f"   💼 근무일: {work_days}일 ({work_percentage:.1f}%)")
        print(f"   ⏰ 총 근무시간: {total_hours}시간")
        
        # 근무 유형별 분포
        shifts_detail = []
        for shift_name, count in stats['shifts'].items():
            if count > 0:
                shifts_detail.append(f"{shift_name}: {count}")
        print(f"   📋 근무 분포: {', '.join(shifts_detail)}")
        
        # 형평성 경고
        if off_percentage > 50:
            print(f"   ⚠️  경고: 휴무 비율이 {off_percentage:.1f}%로 너무 높음!")
        elif off_percentage > 40:
            print(f"   ⚡ 주의: 휴무 비율이 {off_percentage:.1f}%로 높음")
        
        print()
    
    # 전체 형평성 평가
    off_days_list = [stats['off_days'] for stats in staff_stats.values()]
    if off_days_list:
        min_off = min(off_days_list)
        max_off = max(off_days_list)
        avg_off = sum(off_days_list) / len(off_days_list)
        
        print(f"📈 형평성 요약")
        print(f"   최소 휴무일: {min_off}일")
        print(f"   최대 휴무일: {max_off}일") 
        print(f"   평균 휴무일: {avg_off:.1f}일")
        print(f"   편차 범위: {max_off - min_off}일")
        
        if max_off - min_off <= 3:
            print("   ✅ 형평성: 매우 양호 (편차 3일 이하)")
        elif max_off - min_off <= 5:
            print("   ⚡ 형평성: 양호 (편차 5일 이하)")
        else:
            print(f"   ❌ 형평성: 불량 (편차 {max_off - min_off}일)")
    
    return staff_stats

if __name__ == "__main__":
    # 가장 최신 스케줄 파일 찾기
    schedule_files = glob.glob("data/schedule_response_*.json")
    
    if not schedule_files:
        print("❌ 스케줄 파일을 찾을 수 없습니다.")
        exit(1)
    
    # 최신 파일 사용
    latest_file = max(schedule_files)
    print(f"🔍 분석 대상: {latest_file}")
    print()
    
    analyze_schedule_fairness(latest_file)