#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
160시간 제약 적응적 해결 시스템 테스트
"""

import sys
import json
from shift_server_optimized import *

def test_160hour_adaptive_system():
    """160시간 제약에서 적응적 제약조건 시스템 테스트"""
    print("=== 160시간 제약 적응적 해결 시스템 테스트 ===")
    
    # 160시간 제약 테스트 케이스 생성 (10명, 3교대)
    staff_data = {
        'staff': [
            {'name': f'직원{i:02d}', 'staff_id': i, 'grade': 3 if i <= 3 else 4, 'total_hours': 160}
            for i in range(1, 11)
        ]
    }
    
    print(f"🏥 테스트 시나리오: 10명 직원, 160시간/월 제약, 31일 근무표")
    print(f"📊 수학적 분석:")
    print(f"   - 필요 슬롯: 31일 × 3교대 = 93 슬롯")
    print(f"   - 160시간 → 최대 20일/직원")
    print(f"   - 평균 필요: 93 ÷ 10 = 9.3일/직원")
    print(f"   - 여유도: 20 - 9.3 = 10.7일 (이론적으로 가능)")
    print()
    
    try:
        # 직원 데이터 검증
        validated_staff = RequestValidator.validate_staff_data(staff_data)
        print(f"✅ 검증된 직원: {len(validated_staff)}명")
        
        # 교대 규칙 생성
        shift_names = ['Day', 'Evening', 'Night', 'Off']
        position_rules = POSITION_RULES.get('간호', POSITION_RULES['default'])
        shift_rules = RequestValidator.validate_shift_rules({'shifts': shift_names}, position_rules)
        print(f"✅ 교대 시스템: {len(shift_names)}교대 ({', '.join(shift_names)})")
        
        # 적응적 스케줄러 생성 및 실행
        print()
        print("🚀 적응적 제약조건 시스템 시작...")
        scheduler = ShiftScheduler(validated_staff, shift_rules, '간호', 31)
        
        # 해결 시도
        status, solution = scheduler.solve()
        
        print()
        print("=" * 50)
        print(f"🎯 최종 결과: {status.value.upper()}")
        print("=" * 50)
        
        if solution:
            # 성공 시 형평성 분석
            print("✅ 160시간 제약에서도 근무표 생성 성공!")
            print()
            
            # 직원별 근무일 수 계산
            staff_work_days = {}
            staff_off_days = {}
            
            for day_data in solution['schedule']:
                for person in day_data['people']:
                    name = person['name']
                    if day_data['shift'] == 'Off':
                        staff_off_days[name] = staff_off_days.get(name, 0) + 1
                    else:
                        staff_work_days[name] = staff_work_days.get(name, 0) + 1
            
            # 모든 직원이 포함되도록 보장
            for staff_member in validated_staff:
                if staff_member.name not in staff_work_days:
                    staff_work_days[staff_member.name] = 0
                if staff_member.name not in staff_off_days:
                    staff_off_days[staff_member.name] = 0
            
            # 형평성 통계
            work_counts = list(staff_work_days.values())
            off_counts = list(staff_off_days.values())
            
            if work_counts:
                min_work = min(work_counts)
                max_work = max(work_counts)
                avg_work = sum(work_counts) / len(work_counts)
                deviation = max_work - min_work
                
                print("📊 형평성 분석:")
                print(f"   근무일 - 최소: {min_work}일, 최대: {max_work}일, 평균: {avg_work:.1f}일")
                print(f"   편차: {deviation}일 (목표: ±4일 이내)")
                print(f"   휴무일 - 최소: {min(off_counts)}일, 최대: {max(off_counts)}일")
                
                # 160시간 준수 확인
                max_hours = max_work * 8  # 8시간/교대 가정
                print(f"   최대 근무시간: {max_hours}시간 (제한: 160시간)")
                
                if deviation <= 4:
                    print("✅ 형평성 목표 달성 (편차 ±4일 이내)")
                else:
                    print(f"⚠️ 형평성 목표 초과 (편차 {deviation}일)")
                
                if max_hours <= 160:
                    print("✅ 160시간 제약 준수")
                else:
                    print(f"⚠️ 160시간 제약 위반 ({max_hours}시간)")
                
                print()
                print("👥 직원별 상세:")
                for staff_member in validated_staff:
                    name = staff_member.name
                    work_days = staff_work_days.get(name, 0)
                    off_days = staff_off_days.get(name, 0)
                    hours = work_days * 8
                    print(f"   {name}: 근무 {work_days:2d}일 ({hours:3d}시간), 휴무 {off_days:2d}일")
            
        else:
            print("❌ 적응적 시스템으로도 해결 불가")
            print()
            print("💡 추가 해결 방안:")
            print("   1. 직원 수 1-2명 추가")
            print("   2. 교대 패턴 변경 (12시간 교대 등)")
            print("   3. 일부 교대를 선택적으로 운영")
            print("   4. 월 근무시간을 170-180시간으로 조정")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def test_comparison_180hour():
    """180시간 제약과의 비교 테스트"""
    print("\n" + "=" * 60)
    print("📊 180시간 제약과의 비교 테스트")
    print("=" * 60)
    
    # 동일한 직원, 180시간 제약
    staff_data_180 = {
        'staff': [
            {'name': f'직원{i:02d}', 'staff_id': i, 'grade': 3 if i <= 3 else 4, 'total_hours': 180}
            for i in range(1, 11)
        ]
    }
    
    try:
        validated_staff = RequestValidator.validate_staff_data(staff_data_180)
        shift_names = ['Day', 'Evening', 'Night', 'Off']
        position_rules = POSITION_RULES.get('간호', POSITION_RULES['default'])
        shift_rules = RequestValidator.validate_shift_rules({'shifts': shift_names}, position_rules)
        
        print("🔄 180시간 제약으로 테스트 중...")
        scheduler = ShiftScheduler(validated_staff, shift_rules, '간호', 31)
        status, solution = scheduler.solve()
        
        if solution:
            print("✅ 180시간 제약: 근무표 생성 성공")
            
            # 간단한 형평성 분석
            staff_work_days = {}
            for day_data in solution['schedule']:
                for person in day_data['people']:
                    if day_data['shift'] != 'Off':
                        name = person['name']
                        staff_work_days[name] = staff_work_days.get(name, 0) + 1
            
            work_counts = list(staff_work_days.values())
            if work_counts:
                deviation = max(work_counts) - min(work_counts)
                print(f"📊 180시간 제약 편차: {deviation}일")
        else:
            print("❌ 180시간 제약에서도 실패")
            
    except Exception as e:
        print(f"❌ 180시간 테스트 오류: {e}")

if __name__ == "__main__":
    test_160hour_adaptive_system()
    test_comparison_180hour()
    print("\n🎯 테스트 완료!")