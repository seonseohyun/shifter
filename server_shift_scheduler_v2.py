#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 시프트 스케줄러 서버 v2.0
핵심 개선사항:
1. 명시적 시프트 지정 시스템 (night_shifts, off_shifts)
2. 개선된 오류 분석 및 디버깅 정보
3. 프로토콜 호환성 (클라이언트 필드 자동 변환)
4. 안전한 시프트 감지 로직
"""

import socket
import json
from datetime import datetime, timedelta
import calendar
from ortools.sat.python import cp_model
import time

HOST = '127.0.0.1'
PORT = 6004

# 직군별 기본 제약조건
POSITION_RULES = {
    "간호": {
        "newbie_no_night": True,
        "night_after_off": True,
        "max_monthly_hours": 209,
        "newbie_grade": 5,
        "default_shifts": ['D', 'E', 'N', 'O'],
        "default_shift_hours": {'D': 8, 'E': 8, 'N': 8, 'O': 0},
        "default_night_shifts": ['N'],
        "default_off_shifts": ['O']
    },
    "소방": {
        "night_after_off": True,
        "max_monthly_hours": 190,
        "default_shifts": ['D24', 'O'],
        "default_shift_hours": {'D24': 24, 'O': 0},
        "default_night_shifts": ['D24'],
        "default_off_shifts": ['O']
    },
    "default": {
        "night_after_off": True,
        "max_monthly_hours": 180,
        "default_shifts": ['D', 'E', 'N', 'O'],
        "default_shift_hours": {'D': 8, 'E': 8, 'N': 8, 'O': 0},
        "default_night_shifts": ['N'],
        "default_off_shifts": ['O']
    }
}

def normalize_staff_data(staff_data):
    """클라이언트 프로토콜 필드를 서버 형식으로 변환"""
    field_mapping = {
        "staff_uid": "staff_id",
        "job_category": "position", 
        "monthly_workhour": "total_monthly_work_hours"
    }
    
    normalized_staff = []
    for person in staff_data.get("staff", []):
        normalized_person = person.copy()
        
        # 필드명 변환
        for old_field, new_field in field_mapping.items():
            if old_field in normalized_person:
                normalized_person[new_field] = normalized_person.pop(old_field)
        
        normalized_staff.append(normalized_person)
    
    return {"staff": normalized_staff}

def parse_target_month(target_month):
    """target_month 파싱하여 시작일과 일수 계산"""
    try:
        if target_month:
            year, month = map(int, target_month.split('-'))
        else:
            now = datetime.now()
            year, month = now.year, now.month
        
        start_date = datetime(year, month, 1)
        num_days = calendar.monthrange(year, month)[1]
        
        print(f"[INFO] 대상 월: {year}년 {month}월 ({num_days}일)")
        return start_date, num_days
        
    except Exception as e:
        print(f"[ERROR] target_month 파싱 오류: {e}")
        return datetime(2025, 8, 1), 31

def identify_shifts(custom_rules, position_rules):
    """시프트 식별 - 명시적 지정 우선, 폴백으로 자동 감지"""
    
    # 1. 명시적 지정 확인 (최우선)
    if custom_rules:
        night_shifts = custom_rules.get("night_shifts", [])
        off_shifts = custom_rules.get("off_shifts", [])
        
        if night_shifts or off_shifts:
            print(f"[INFO] 명시적 시프트 지정:")
            print(f"  - 야간 시프트: {night_shifts}")
            print(f"  - 휴무 시프트: {off_shifts}")
            return night_shifts, off_shifts
    
    # 2. 시프트 목록에서 자동 감지 (개선된 로직)
    shifts = custom_rules.get("shifts", position_rules.get("default_shifts", []))
    
    # 안전한 키워드 매칭 (단어 완성도와 길이 고려)
    night_keywords = ['night', 'nocturnal', '야간', '밤', '심야']  # 3글자 이상
    off_keywords = ['off', 'rest', 'free', '휴무', '쉼', '오프']   # 3글자 이상
    
    # 정확한 축약형 매핑
    night_abbrev = {'n': 'night', 'nt': 'night'}
    off_abbrev = {'o': 'off', 'r': 'rest'}
    
    detected_night = []
    detected_off = []
    
    print(f"[INFO] 시프트 자동 감지 중: {shifts}")
    
    for shift in shifts:
        shift_lower = shift.lower()
        
        # 야간 시프트 감지
        is_night = False
        if shift_lower in night_abbrev:
            detected_night.append(shift)
            is_night = True
            print(f"  '{shift}' → 야간 (축약형: {night_abbrev[shift_lower]})")
        else:
            for keyword in night_keywords:
                if keyword.lower() in shift_lower and len(keyword) >= 3:
                    detected_night.append(shift)
                    is_night = True
                    print(f"  '{shift}' → 야간 (키워드: {keyword})")
                    break
        
        # 휴무 시프트 감지 (야간이 아닌 경우에만)
        if not is_night:
            if shift_lower in off_abbrev:
                detected_off.append(shift)
                print(f"  '{shift}' → 휴무 (축약형: {off_abbrev[shift_lower]})")
            else:
                for keyword in off_keywords:
                    if keyword.lower() in shift_lower and len(keyword) >= 3:
                        detected_off.append(shift)
                        print(f"  '{shift}' → 휴무 (키워드: {keyword})")
                        break
    
    # 3. 기본값 사용 (감지 실패 시)
    if not detected_night and not detected_off:
        detected_night = position_rules.get("default_night_shifts", [])
        detected_off = position_rules.get("default_off_shifts", [])
        print(f"[INFO] 기본값 사용: 야간={detected_night}, 휴무={detected_off}")
    
    return detected_night, detected_off

def validate_request_parameters(staff_data, position, custom_rules):
    """요청 파라미터 상세 검증 및 오류 분석"""
    errors = []
    warnings = []
    
    # 1. 기본 필수 필드 검증
    if not staff_data or "staff" not in staff_data:
        errors.append("staff_data.staff 필드가 없거나 비어있음")
        return errors, warnings
    
    staff_list = staff_data["staff"]
    if not isinstance(staff_list, list) or len(staff_list) == 0:
        errors.append("직원 데이터가 비어있음")
        return errors, warnings
    
    # 2. 직원별 필수 필드 검증
    required_fields = ["name", "staff_id", "position", "total_monthly_work_hours"]
    for i, person in enumerate(staff_list):
        for field in required_fields:
            if field not in person:
                errors.append(f"직원 {i+1}: '{field}' 필드 누락")
    
    # 3. 시프트 설정 검증
    if custom_rules:
        shifts = custom_rules.get("shifts", [])
        shift_hours = custom_rules.get("shift_hours", {})
        
        if not shifts:
            warnings.append("custom_rules.shifts가 비어있음, 기본값 사용")
        else:
            # 시프트-시간 매핑 확인
            missing_hours = [s for s in shifts if s not in shift_hours]
            if missing_hours:
                errors.append(f"시프트 시간 정보 누락: {missing_hours}")
            
            # 최대 근무시간 계산
            work_hours = [shift_hours.get(s, 0) for s in shifts if shift_hours.get(s, 0) > 0]
            daily_max = sum(work_hours)
            
            if daily_max <= 0:
                errors.append("하루 총 근무시간이 0시간 (모든 시프트가 휴무)")
            elif daily_max > 24:
                warnings.append(f"하루 총 근무시간이 24시간 초과: {daily_max}시간")
    
    # 4. 직군별 제약 확인
    position_rules = POSITION_RULES.get(position, POSITION_RULES["default"])
    max_monthly = position_rules.get("max_monthly_hours", 180)
    
    for person in staff_list:
        monthly_hours = person.get("total_monthly_work_hours", 0)
        if monthly_hours > max_monthly:
            warnings.append(f"{person.get('name', '미명')}: 월 근무시간 {monthly_hours}h > 한도 {max_monthly}h")
    
    return errors, warnings

def apply_constraints(model, schedule, staff_data, shifts, shift_hours, days, position, night_shifts, off_shifts):
    """제약조건 적용"""
    position_rules = POSITION_RULES.get(position, POSITION_RULES["default"])
    staff_list = staff_data["staff"]
    
    print(f"[INFO] 제약조건 적용 시작 ({position} 직군)")
    print(f"[INFO] 야간 시프트: {night_shifts}")
    print(f"[INFO] 휴무 시프트: {off_shifts}")
    
    # 각 날짜, 각 시프트마다 최소 1명 배정
    for day in days:
        for shift in shifts:
            if shift not in off_shifts:  # 휴무는 제외
                shift_vars = [schedule[(str(person["staff_id"]), day, shift)] for person in staff_list]
                model.Add(sum(shift_vars) >= 1)
    
    # 개인별 제약조건
    for person in staff_list:
        staff_id = str(person["staff_id"])
        grade = person.get("grade", 1)
        name = person.get("name", f"staff_{staff_id}")
        
        print(f"[INFO] {name} 제약조건 적용...")
        
        # 하루에 하나의 시프트만 배정
        for day in days:
            day_shifts = [schedule[(staff_id, day, shift)] for shift in shifts]
            model.Add(sum(day_shifts) == 1)
        
        # 신규간호사 야간 근무 금지 (간호직군)
        if position == "간호" and position_rules.get("newbie_no_night", False):
            if grade == position_rules.get("newbie_grade", 5):
                for night_shift in night_shifts:
                    if night_shift in shifts:
                        for day in days:
                            model.Add(schedule[(staff_id, day, night_shift)] == 0)
                if night_shifts:
                    print(f"[INFO] {name}: 신규간호사 야간 근무 금지 (대상: {night_shifts})")
        
        # 야간 근무 후 휴무 제약
        # if position_rules.get("night_after_off", False) and night_shifts and off_shifts:
        #     for day in range(len(days) - 1):
        #         night_vars = [schedule[(staff_id, day, ns)] for ns in night_shifts if ns in shifts]
        #         off_next_vars = [schedule[(staff_id, day + 1, os)] for os in off_shifts if os in shifts]
                
        #         if night_vars and off_next_vars:
        #             # 야간 근무 → 다음날 휴무 중 하나 (수정된 로직)
        #             total_night = sum(night_vars)
        #             total_off_next = sum(off_next_vars)
        #             # 야간 근무가 있으면 다음날 휴무가 있어야 함
        #             model.Add(total_night <= total_off_next)

        # 야간 근무 후 휴무 제약
        if position_rules.get("night_after_off", False) and night_shifts and off_shifts:
            for day in range(len(days) - 1):
                night_vars = [schedule[(staff_id, day, ns)] for ns in night_shifts if ns in shifts]
                off_next_vars = [schedule[(staff_id, day + 1, os)] for os in off_shifts if os in shifts]
                
                if night_vars and off_next_vars:
                    # 기존 로직: 야간 근무가 있으면 다음날 휴무가 있어야 함
                    total_night = sum(night_vars)
                    total_off_next = sum(off_next_vars)
                    model.Add(total_night <= total_off_next)
                    
                    # 추가 제약: 야간 후 다음 날 비야간/비휴무 근무 금지 (동적 루프)
                    for other_shift in shifts:
                        if other_shift not in off_shifts and other_shift not in night_shifts:
                            next_shift = schedule[(staff_id, day + 1, other_shift)]
                            # 야간 근무 중 하나라도 있으면, 해당 other_shift 금지
                            for night_var in night_vars:
                                model.AddBoolOr([night_var.Not(), next_shift.Not()])

        
        # 월간 근무시간 제한
        monthly_limit = person.get("total_monthly_work_hours", position_rules.get("max_monthly_hours", 180))
        work_hours = []
        for day in days:
            for shift in shifts:
                hours = shift_hours.get(shift, 0)
                if hours > 0:
                    work_hours.append(schedule[(staff_id, day, shift)] * hours)
        
        if work_hours:
            model.Add(sum(work_hours) <= monthly_limit)

def analyze_infeasible_model(staff_data, shifts, shift_hours, days, position, night_shifts, off_shifts):
    """INFEASIBLE 모델 상세 분석"""
    analysis = {
        "basic_info": {
            "staff_count": len(staff_data["staff"]),
            "days": len(days),
            "shifts": shifts,
            "work_shifts": [s for s in shifts if s not in off_shifts]
        },
        "capacity_analysis": {},
        "constraint_analysis": {},
        "identified_issues": []
    }
    
    # 용량 분석
    work_shifts = [s for s in shifts if s not in off_shifts]
    daily_slots_needed = len(work_shifts)  # 각 근무 시프트마다 최소 1명
    total_slots_needed = daily_slots_needed * len(days)
    
    # 개인별 가용 시간 계산
    staff_availability = []
    for person in staff_data["staff"]:
        monthly_limit = person.get("total_monthly_work_hours", 180)
        max_work_days = monthly_limit // 8 if monthly_limit > 0 else 0  # 8시간/일 기준
        staff_availability.append(max_work_days)
    
    total_capacity = sum(staff_availability)
    
    analysis["capacity_analysis"] = {
        "daily_slots_needed": daily_slots_needed,
        "total_slots_needed": total_slots_needed,
        "total_staff_capacity": total_capacity,
        "capacity_ratio": total_capacity / total_slots_needed if total_slots_needed > 0 else 0
    }
    
    # 문제 식별
    if total_capacity < total_slots_needed:
        analysis["identified_issues"].append(f"용량 부족: 필요 {total_slots_needed}일 vs 가능 {total_capacity}일")
    
    # 신규간호사 야간 제약 분석 (간호직군)
    if position == "간호" and night_shifts:
        newbies = [p for p in staff_data["staff"] if p.get("grade", 1) == 5]
        veterans = [p for p in staff_data["staff"] if p.get("grade", 1) != 5]
        
        night_slots_needed = len(night_shifts) * len(days)
        veteran_capacity = len(veterans) * len(days)
        
        analysis["constraint_analysis"]["newbie_restriction"] = {
            "newbie_count": len(newbies),
            "veteran_count": len(veterans),
            "night_slots_needed": night_slots_needed,
            "veteran_capacity": veteran_capacity
        }
        
        if veteran_capacity < night_slots_needed:
            analysis["identified_issues"].append(f"베테랑 부족: 야간 {night_slots_needed}슬롯 vs 베테랑 용량 {veteran_capacity}")
    
    return analysis

def generate_shift_schedule(request_data):
    """시프트 스케줄 생성 메인 함수"""
    start_time = time.time()
    
    try:
        # 1. 요청 데이터 정규화
        raw_staff_data = request_data.get("staff_data", {})
        staff_data = normalize_staff_data(raw_staff_data)
        
        position = request_data.get("position", "default")
        target_month = request_data.get("target_month", None)
        custom_rules = request_data.get("custom_rules", {})
        
        print(f"[INFO] === 시프트 스케줄 생성 시작 ===")
        print(f"[INFO] 직군: {position}")
        print(f"[INFO] 직원 수: {len(staff_data.get('staff', []))}명")
        
        # 2. 파라미터 검증
        errors, warnings = validate_request_parameters(staff_data, position, custom_rules)
        
        if errors:
            return {
                "result": "생성실패",
                "reason": f"입력 데이터 오류: {'; '.join(errors)}",
                "status": "error",
                "details": {
                    "solver_status": "INVALID_INPUT",
                    "validation_errors": errors,
                    "validation_warnings": warnings,
                    "solve_time": f"{time.time() - start_time:.2f}초"
                }
            }
        
        if warnings:
            print(f"[WARN] 경고사항: {'; '.join(warnings)}")
        
        # 3. 기본 설정
        start_date, num_days = parse_target_month(target_month)
        days = list(range(num_days))
        
        position_rules = POSITION_RULES.get(position, POSITION_RULES["default"])
        shifts = custom_rules.get("shifts", position_rules["default_shifts"])
        shift_hours = custom_rules.get("shift_hours", position_rules["default_shift_hours"])
        
        # 4. 시프트 식별
        night_shifts, off_shifts = identify_shifts(custom_rules, position_rules)
        
        # 5. CP-SAT 모델 생성
        model = cp_model.CpModel()
        schedule = {}
        
        # 변수 생성
        for person in staff_data["staff"]:
            staff_id = str(person["staff_id"])
            for day in days:
                for shift in shifts:
                    schedule[(staff_id, day, shift)] = model.NewBoolVar(f'schedule_{staff_id}_{day}_{shift}')
        
        # 6. 제약조건 적용
        apply_constraints(model, schedule, staff_data, shifts, shift_hours, days, position, night_shifts, off_shifts)
        
        # 7. 솔버 실행
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30.0  # 30초 제한
        
        print(f"[INFO] CP-SAT 솔버 실행 중...")
        status = solver.Solve(model)
        solve_time = time.time() - start_time
        
        print(f"[INFO] 솔버 상태: {solver.StatusName(status)}")
        print(f"[INFO] 처리 시간: {solve_time:.2f}초")
        
        # 8. 결과 처리
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            # 성공 - 스케줄 생성
            result_schedule = {}
            for day in days:
                date_str = (start_date + timedelta(days=day)).strftime('%Y-%m-%d')
                result_schedule[date_str] = []
                
                for shift in shifts:
                    people = []
                    for person in staff_data["staff"]:
                        staff_id = str(person["staff_id"])
                        if solver.Value(schedule[(staff_id, day, shift)]):
                            people.append({
                                "이름": person["name"],
                                "직원번호": person["staff_id"],
                                "등급": person.get("grade", 1),
                                "grade": person.get("grade", 1)  # test_recommended.py 호환성
                            })
                    
                    if people:  # 배정된 사람이 있는 시프트만 포함
                        result_schedule[date_str].append({
                            "shift": shift,
                            "hours": shift_hours.get(shift, 0),
                            "people": people
                        })
            
            return {
                "status": "ok",
                "schedule": result_schedule,
                "details": {
                    "solver_status": solver.StatusName(status),
                    "solve_time": f"{solve_time:.2f}초",
                    "staff_count": len(staff_data["staff"]),
                    "shifts_identified": {
                        "night_shifts": night_shifts,
                        "off_shifts": off_shifts
                    }
                }
            }
        
        else:
            # 실패 - 상세 분석
            analysis = analyze_infeasible_model(staff_data, shifts, shift_hours, days, position, night_shifts, off_shifts)
            
            return {
                "result": "생성실패",
                "reason": f"수학적 모델 해결 불가 ({solver.StatusName(status)})",
                "status": "error", 
                "details": {
                    "solver_status": solver.StatusName(status),
                    "solve_time": f"{solve_time:.2f}초",
                    "staff_count": len(staff_data["staff"]),
                    "analysis": analysis,
                    "identified_issues": analysis["identified_issues"],
                    "suggestions": [
                        "직원 수 증가 또는 근무시간 한도 상향 조정",
                        "시프트 구조 단순화 (시프트 수 줄이기)",
                        "제약조건 완화 (신규간호사 야간근무 허용 등)"
                    ]
                }
            }
    
    except Exception as e:
        solve_time = time.time() - start_time
        print(f"[ERROR] 예외 발생: {e}")
        return {
            "result": "생성실패",
            "reason": f"서버 내부 오류: {str(e)}",
            "status": "error",
            "details": {
                "solver_status": "EXCEPTION",
                "solve_time": f"{solve_time:.2f}초",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        }

def handle_client(conn, addr):
    """클라이언트 연결 처리"""
    try:
        print(f"[INFO] 클라이언트 연결: {addr}")
        
        # 데이터 수신
        data = b''
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        
        if not data:
            print(f"[WARN] {addr}: 빈 요청")
            return
        
        # JSON 파싱
        try:
            request_data = json.loads(data.decode('utf-8'))
        except json.JSONDecodeError as e:
            error_response = {
                "result": "생성실패",
                "reason": f"JSON 파싱 오류: {str(e)}",
                "status": "error"
            }
            response = json.dumps(error_response, ensure_ascii=False)
            conn.sendall(response.encode('utf-8'))
            return
        
        # 스케줄 생성
        result = generate_shift_schedule(request_data)
        
        # 응답 전송
        response = json.dumps(result, ensure_ascii=False, indent=2)
        conn.sendall(response.encode('utf-8'))
        
        print(f"[INFO] {addr}: 응답 완료 ({result.get('status', 'unknown')})")
        
    except Exception as e:
        print(f"[ERROR] 클라이언트 처리 오류 {addr}: {e}")
        try:
            error_response = {
                "result": "생성실패",
                "reason": f"서버 처리 오류: {str(e)}",
                "status": "error"
            }
            response = json.dumps(error_response, ensure_ascii=False)
            conn.sendall(response.encode('utf-8'))
        except:
            pass
    finally:
        conn.close()

def main():
    """메인 서버 함수"""
    print(f"[INFO] 시프트 스케줄러 서버 v2.0 시작")
    print(f"[INFO] 수신 대기: {HOST}:{PORT}")
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        
        print(f"[INFO] 서버 준비 완료")
        
        while True:
            try:
                conn, addr = server_socket.accept()
                handle_client(conn, addr)
            except KeyboardInterrupt:
                print(f"\n[INFO] 서버 종료 중...")
                break
            except Exception as e:
                print(f"[ERROR] 연결 수락 오류: {e}")
                continue
    
    except Exception as e:
        print(f"[ERROR] 서버 시작 오류: {e}")
    
    finally:
        server_socket.close()
        print(f"[INFO] 서버 종료됨")

if __name__ == "__main__":
    main()