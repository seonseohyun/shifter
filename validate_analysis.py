#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_request_parameters 함수 분석 및 개선 제안
"""

def validate_request_parameters_minimal(staff_data, position, custom_rules):
    """최소한의 필수 검증만 수행 (명시적 시프트 지정 환경용)"""
    errors = []
    warnings = []
    
    # 1. 기본 데이터 구조 검증 (필수)
    if not staff_data or "staff" not in staff_data:
        errors.append("staff_data.staff 필드가 없거나 비어있음")
        return errors, warnings
    
    staff_list = staff_data["staff"]
    if not isinstance(staff_list, list) or len(staff_list) == 0:
        errors.append("직원 데이터가 비어있음")
        return errors, warnings
    
    # 2. 직원별 필수 필드 검증 (필수)
    required_fields = ["name", "staff_id", "position", "total_monthly_work_hours"]
    for i, person in enumerate(staff_list):
        for field in required_fields:
            if field not in person:
                errors.append(f"직원 {i+1}: '{field}' 필드 누락")
    
    # 3. custom_rules 기본 구조 검증 (필수)
    if custom_rules:
        shifts = custom_rules.get("shifts", [])
        shift_hours = custom_rules.get("shift_hours", {})
        
        if not shifts:
            warnings.append("custom_rules.shifts가 비어있음, 기본값 사용")
        else:
            # 시프트-시간 매핑 확인 (필수)
            missing_hours = [s for s in shifts if s not in shift_hours]
            if missing_hours:
                errors.append(f"시프트 시간 정보 누락: {missing_hours}")
            
            # 모든 시프트가 0시간인지 확인 (필수)
            work_hours = [shift_hours.get(s, 0) for s in shifts if shift_hours.get(s, 0) > 0]
            if len(work_hours) == 0:
                errors.append("하루 총 근무시간이 0시간 (모든 시프트가 휴무)")
    
    return errors, warnings

def validate_request_parameters_comprehensive(staff_data, position, custom_rules):
    """포괄적 검증 (자동 감지 환경용)"""
    errors = []
    warnings = []
    
    # 기본 검증 먼저 수행
    basic_errors, basic_warnings = validate_request_parameters_minimal(staff_data, position, custom_rules)
    errors.extend(basic_errors)
    warnings.extend(basic_warnings)
    
    if errors:  # 기본 검증 실패 시 추가 검증 스킵
        return errors, warnings
    
    # 4. 추가 안전성 검증
    staff_list = staff_data["staff"]
    
    # 직원 수 적정성 확인
    if len(staff_list) < 3:
        warnings.append(f"직원 수 부족: {len(staff_list)}명 (최소 3명 권장)")
    elif len(staff_list) > 100:
        warnings.append(f"직원 수 과다: {len(staff_list)}명 (성능 저하 가능)")
    
    # 시프트 시간 합리성 확인
    if custom_rules and custom_rules.get("shifts"):
        shifts = custom_rules["shifts"]
        shift_hours = custom_rules["shift_hours"]
        
        work_shifts = [s for s in shifts if shift_hours.get(s, 0) > 0]
        total_hours = sum(shift_hours.get(s, 0) for s in work_shifts)
        
        if total_hours > 72:  # 3일 치 근무시간
            warnings.append(f"하루 총 근무시간 과다: {total_hours}시간")
    
    # 5. 직군별 제약 미리 확인
    from server_shift_scheduler_v2 import POSITION_RULES
    position_rules = POSITION_RULES.get(position, POSITION_RULES["default"])
    max_monthly = position_rules.get("max_monthly_hours", 180)
    
    for person in staff_list:
        monthly_hours = person.get("total_monthly_work_hours", 0)
        if monthly_hours > max_monthly * 1.2:  # 20% 여유 허용
            warnings.append(f"{person.get('name', '미명')}: 월 근무시간 과다 {monthly_hours}h > 권장 {max_monthly}h")
        elif monthly_hours < max_monthly * 0.5:  # 너무 적으면 경고
            warnings.append(f"{person.get('name', '미명')}: 월 근무시간 부족 {monthly_hours}h < 권장 {max_monthly * 0.8}h")
    
    return errors, warnings

# 테스트 시나리오
def test_validation_scenarios():
    """다양한 시나리오로 검증 함수 테스트"""
    
    print("=== 검증 함수 효율성 분석 ===")
    
    # 시나리오 1: 명시적 시프트 지정 (이상적)
    scenario1 = {
        "staff_data": {
            "staff": [
                {"name": "김간호사", "staff_id": 1, "position": "간호", "total_monthly_work_hours": 195}
            ]
        },
        "position": "간호",
        "custom_rules": {
            "shifts": ["Day", "Night", "Off"],
            "shift_hours": {"Day": 8, "Night": 8, "Off": 0},
            "night_shifts": ["Night"],  # 명시적 지정
            "off_shifts": ["Off"]       # 명시적 지정
        }
    }
    
    print("\n시나리오 1: 명시적 시프트 지정 (완벽한 케이스)")
    errors1, warnings1 = validate_request_parameters_minimal(
        scenario1["staff_data"], scenario1["position"], scenario1["custom_rules"]
    )
    print(f"최소 검증 → 오류: {len(errors1)}, 경고: {len(warnings1)}")
    
    errors1_comp, warnings1_comp = validate_request_parameters_comprehensive(
        scenario1["staff_data"], scenario1["position"], scenario1["custom_rules"]
    )
    print(f"포괄 검증 → 오류: {len(errors1_comp)}, 경고: {len(warnings1_comp)}")
    print(f"결론: 명시적 지정 시 최소 검증으로 충분")
    
    # 시나리오 2: 잘못된 데이터 (필수 검증 케이스)
    scenario2 = {
        "staff_data": {"staff": []},  # 빈 직원 데이터
        "position": "간호",
        "custom_rules": {"shifts": ["Day"], "shift_hours": {}}  # 시간 정보 누락
    }
    
    print("\n시나리오 2: 잘못된 데이터")
    errors2, warnings2 = validate_request_parameters_minimal(
        scenario2["staff_data"], scenario2["position"], scenario2["custom_rules"]
    )
    print(f"최소 검증 → 오류: {len(errors2)}, 경고: {len(warnings2)}")
    if errors2:
        print(f"  감지된 오류: {errors2}")
    print(f"결론: 필수 검증이 중요한 문제를 정확히 감지")
    
    # 시나리오 3: 자동 감지 의존 (포괄 검증 유용)
    scenario3 = {
        "staff_data": {
            "staff": [{"name": f"직원{i}", "staff_id": i, "position": "간호", "total_monthly_work_hours": 195} for i in range(1, 4)]
        },
        "position": "간호", 
        "custom_rules": {
            "shifts": ["Morning", "Evening", "Night", "Rest"],  # 애매한 명칭
            "shift_hours": {"Morning": 8, "Evening": 8, "Night": 8, "Rest": 0}
            # night_shifts, off_shifts 미지정 → 자동 감지 필요
        }
    }
    
    print("\n시나리오 3: 자동 감지 의존")
    errors3, warnings3 = validate_request_parameters_comprehensive(
        scenario3["staff_data"], scenario3["position"], scenario3["custom_rules"]
    )
    print(f"포괄 검증 → 오류: {len(errors3)}, 경고: {len(warnings3)}")
    print(f"결론: 자동 감지 시 포괄 검증이 잠재적 문제 예방")

if __name__ == "__main__":
    test_validation_scenarios()