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
import os
from openai import OpenAI

HOST = '127.0.0.1'
PORT = 6004

# OpenAI 설정
# 환경변수에서 API 키를 가져오거나 기본값 설정
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-proj-your-api-key-here')  # 실제 키로 변경 필요
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY != 'sk-proj-your-api-key-here' else None

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
    """요청 파라미터 필수 검증 (명시적 시프트 지정 환경 최적화)"""
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
    
    # 2. 직원별 필수 필드 검증 (필수) - position은 data 레벨에서 추가되므로 검증에서 확인
    required_fields = ["name", "staff_id", "total_monthly_work_hours", "position", "grade"]
    optional_fields = ["grade_name"]  # 선택적 필드
    
    for i, person in enumerate(staff_list):
        for field in required_fields:
            if field not in person:
                errors.append(f"직원 {i+1}: '{field}' 필드 누락")
        
        # 선택적 필드는 로그만 (경고 제거)
        # for field in optional_fields:
        #     if field not in person:
        #         warnings.append(f"직원 {i+1}: '{field}' 필드 없음 (선택사항)")
                
        # 데이터 타입 검증 (안전성)
        if "total_monthly_work_hours" in person:
            try:
                hours = person["total_monthly_work_hours"]
                if not isinstance(hours, (int, float)) or hours < 0:
                    errors.append(f"직원 {i+1}: 월 근무시간이 유효하지 않음 ({hours})")
            except (ValueError, TypeError):
                errors.append(f"직원 {i+1}: 월 근무시간 형식 오류")
    
    # 3. custom_rules 기본 구조 검증 (필수)
    if custom_rules:
        shifts = custom_rules.get("shifts", [])
        shift_hours = custom_rules.get("shift_hours", {})
        
        if not shifts:
            warnings.append("shifts가 비어있음, 기본값 사용")
        else:
            # 시프트-시간 매핑 확인 (필수)
            missing_hours = [s for s in shifts if s not in shift_hours]
            if missing_hours:
                errors.append(f"시프트 시간 정보 누락: {missing_hours}")
            
            # 모든 시프트가 0시간인지만 확인 (필수)
            work_hours = [shift_hours.get(s, 0) for s in shifts if shift_hours.get(s, 0) > 0]
            if len(work_hours) == 0:
                errors.append("모든 시프트가 휴무 (근무 시프트 없음)")
            
            # 시프트 시간 범위 검증 (안전성)
            for shift, hours in shift_hours.items():
                if not isinstance(hours, (int, float)) or hours < 0 or hours > 24:
                    errors.append(f"시프트 '{shift}': 근무시간이 유효하지 않음 ({hours}시간)")
    
    # 4. 직원 수 적정성 확인 (경고만)
    if len(staff_list) < 3:
        warnings.append(f"직원 수 부족: {len(staff_list)}명 (최소 3명 권장)")
    
    return errors, warnings

def apply_constraints(model, schedule, staff_data, shifts, shift_hours, days, position, night_shifts, off_shifts):
    """제약조건 적용"""
    position_rules = POSITION_RULES.get(position, POSITION_RULES["default"])
    staff_list = staff_data["staff"]
    
    print(f"[INFO] 제약조건 적용 시작 ({position} 직군)")
    print(f"[INFO] 야간 시프트: {night_shifts}")
    print(f"[INFO] 휴무 시프트: {off_shifts}")
    
    # 엣지 케이스 검증
    if len(days) < 2:
        print(f"[WARN] 근무일 수가 너무 적음: {len(days)}일, 일부 제약 스킵")
    
    if not night_shifts:
        print(f"[WARN] 야간 시프트가 없음, 야간 관련 제약 스킵")
    
    if not off_shifts:
        print(f"[WARN] 휴무 시프트가 없음, 휴무 관련 제약 스킵")
    
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
    
    # 소방 직군 전용 제약조건
    if position == "소방":
        print(f"[INFO] 소방 직군 제약조건 적용")
        
        # D24 (24시간 당직) 시프트 식별
        duty_shifts = [s for s in shifts if "d24" in s.lower() or "24" in s.lower() or "당직" in s.lower()]
        if not duty_shifts:
            duty_shifts = night_shifts  # 폴백: 야간 시프트를 당직으로 처리
        
        if duty_shifts and off_shifts and len(days) >= 3:
            print(f"[INFO] 소방 당직 시프트: {duty_shifts}")
            
            for person in staff_list:
                staff_id = str(person["staff_id"])
                name = person.get("name", f"staff_{staff_id}")
                
                # 24시간 당직 후 최소 1일 이상 휴무
                for day in range(len(days) - 1):
                    duty_vars = [schedule[(staff_id, day, ds)] for ds in duty_shifts if ds in shifts]
                    off_next_vars = [schedule[(staff_id, day + 1, os)] for os in off_shifts if os in shifts]
                    
                    if duty_vars and off_next_vars:
                        total_duty = sum(duty_vars)
                        total_off_next = sum(off_next_vars)
                        # 당직 근무 → 다음날 휴무 필수
                        model.Add(total_duty <= total_off_next)
                
                # 월 당직 횟수 제한 (8-12회 권장, 최대 15회)
                monthly_duty_count = []
                for day in days:
                    for duty_shift in duty_shifts:
                        if duty_shift in shifts:
                            monthly_duty_count.append(schedule[(staff_id, day, duty_shift)])
                
                if monthly_duty_count:
                    model.Add(sum(monthly_duty_count) <= 15)  # 최대 15회
                    model.Add(sum(monthly_duty_count) >= 6)   # 최소 6회
                    
            print(f"[INFO] 소방 제약 적용 완료: 당직 후 휴무, 월 6-15회 제한")

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

def save_request_to_file(request_data, client_addr):
    """요청 데이터를 data 디렉토리에 저장"""
    try:
        os.makedirs("data", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/server_request_{timestamp}_{client_addr[0]}_{client_addr[1]}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(request_data, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 📝 요청 데이터 저장: {filename}")
        return filename
    except Exception as e:
        print(f"[WARN] 요청 데이터 저장 실패: {e}")
        return None

def save_response_to_file(response_data, client_addr):
    """응답 데이터를 data 디렉토리에 저장"""
    try:
        os.makedirs("data", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/server_response_{timestamp}_{client_addr[0]}_{client_addr[1]}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 📝 응답 데이터 저장: {filename}")
        return filename
    except Exception as e:
        print(f"[WARN] 응답 데이터 저장 실패: {e}")
        return None

def summarize_handover(input_text):
    """OpenAI를 활용한 인수인계 내용 요약"""
    start_time = time.time()
    
    try:
        # OpenAI 클라이언트 체크
        if openai_client is None:
            return {
                "status": "error",
                "task": "summarize_handover", 
                "reason": "OpenAI API 키가 설정되지 않았습니다."
            }
        
        # 입력 검증
        if not input_text or input_text.strip() == "":
            return {
                "status": "error",
                "task": "summarize_handover",
                "reason": "input_text가 비어 있습니다."
            }
        
        print(f"[INFO] === 인수인계 요약 시작 ===")
        print(f"[INFO] 입력 텍스트 길이: {len(input_text)} 문자")
        
        # Master Handover AI 프롬프트
        system_prompt = """넌 Master Handover AI야. 
간결하고 명확하게 인수인계 내용을 요약하는 전문가야.

입력된 내용을 빠르게 파악할 수 있도록 핵심만 뽑아 요약해줘.  
중요한 일정, 변경사항, 위험요소는 우선순위로 정리하고,  
불필요한 말은 생략하고 실무에 바로 도움이 되도록 써줘."""
        
        # OpenAI API 호출
        print(f"[INFO] OpenAI API 호출 중...")
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        process_time = time.time() - start_time
        
        print(f"[INFO] 요약 완료: {process_time:.2f}초")
        print(f"[INFO] 요약 결과 길이: {len(summary)} 문자")
        
        return {
            "status": "success",
            "task": "summarize_handover",
            "result": summary
        }
        
    except Exception as e:
        process_time = time.time() - start_time
        print(f"[ERROR] 인수인계 요약 오류 ({process_time:.2f}초): {e}")
        return {
            "status": "error",
            "task": "summarize_handover", 
            "reason": f"요약 처리 중 오류 발생: {str(e)}"
        }

def process_request(request_data):
    """요청 처리 메인 함수 - task 기반 라우팅"""
    start_time = time.time()
    
    try:
        print(f"[INFO] === 요청 처리 시작 ===")
        
        # 1. 요청 타입 확인
        if "task" in request_data:
            # Task 기반 요청 (인수인계 요약 등)
            task = request_data.get("task", "")
            print(f"[INFO] Task 요청: {task}")
            
            if task == "summarize_handover":
                input_text = request_data.get("input_text", "")
                return summarize_handover(input_text)
            else:
                return {
                    "status": "error",
                    "task": task,
                    "reason": f"알 수 없는 task: {task}"
                }
        
        elif "protocol" in request_data and "data" in request_data:
            # 기존 프로토콜 기반 요청 (스케줄 생성)
            return generate_shift_schedule(request_data)
        
        else:
            # 직접 스케줄 생성 요청 (Python 클라이언트)
            return generate_shift_schedule(request_data)
            
    except Exception as e:
        process_time = time.time() - start_time
        print(f"[ERROR] 요청 처리 오류 ({process_time:.2f}초): {e}")
        return {
            "status": "error",
            "reason": f"요청 처리 중 오류 발생: {str(e)}"
        }

def generate_shift_schedule(request_data):
    """시프트 스케줄 생성 메인 함수"""
    start_time = time.time()
    
    try:
        # 1. C++ 프로토콜 호환성 처리
        if "protocol" in request_data and "data" in request_data:
            # C++ 클라이언트 프로토콜 (data 래퍼 존재)
            protocol = request_data.get("protocol", "")
            actual_data = request_data.get("data", {})
            print(f"[INFO] C++ 프로토콜 요청: {protocol}")
            
            # py_gen_timetable 요청을 py_gen_schedule 응답으로 처리
            if protocol == "py_gen_timetable":
                print(f"[INFO] 근무표 생성 요청 처리 중...")
        else:
            # Python 클라이언트 프로토콜 (직접 데이터)
            actual_data = request_data
            protocol = "python_direct"
        
        # 2. 요청 데이터 정규화
        raw_staff_data = actual_data.get("staff_data", {})
        staff_data = normalize_staff_data(raw_staff_data)
        
        # position은 data 레벨에서 가져옴 (프로토콜 규격 준수)
        position = actual_data.get("position", "default")
        target_month = actual_data.get("target_month", None)
        custom_rules = actual_data.get("custom_rules", {})
        
        # staff_data의 모든 직원에 position 정보 추가 (내부 처리용)
        if "staff" in staff_data:
            for person in staff_data["staff"]:
                person["position"] = position
        
        print(f"[INFO] === 시프트 스케줄 생성 시작 ===")
        print(f"[INFO] 직군: {position}")
        print(f"[INFO] 직원 수: {len(staff_data.get('staff', []))}명")
        
        # 3. 파라미터 검증 (position 추가 후 실행)
        errors, warnings = validate_request_parameters(staff_data, position, custom_rules)
        
        if errors:
            validation_error_response = {
                "protocol": "py_gen_schedule",
                "resp": "fail",
                "data": []
            }
            
            return validation_error_response
        
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
            schedule_data = []
            for day in days:
                date_str = (start_date + timedelta(days=day)).strftime('%Y-%m-%d')
                
                for shift in shifts:
                    people = []
                    for person in staff_data["staff"]:
                        staff_id = str(person["staff_id"])
                        if solver.Value(schedule[(staff_id, day, shift)]):
                            person_info = {
                                "name": person["name"],
                                "staff_id": person["staff_id"],
                                "grade": person.get("grade", 1)
                            }
                            people.append(person_info)
                    
                    if people:  # 배정된 사람이 있는 시프트만 포함
                        schedule_data.append({
                            "date": date_str,
                            "shift": shift,
                            "hours": shift_hours.get(shift, 0),
                            "people": people
                        })
            
            response = {
                "protocol": "py_gen_schedule",
                "resp": "success",
                "data": schedule_data
            }
            
            return response
        
        else:
            # 실패 - 상세 분석
            analysis = analyze_infeasible_model(staff_data, shifts, shift_hours, days, position, night_shifts, off_shifts)
            
            error_response = {
                "protocol": "py_gen_schedule",
                "resp": "fail",
                "data": []
            }
            
            return error_response
    
    except Exception as e:
        solve_time = time.time() - start_time
        print(f"[ERROR] 예외 발생: {e}")
        exception_response = {
            "protocol": "py_gen_schedule",
            "resp": "fail",
            "data": []
        }
        
        return exception_response

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
        
        # JSON 파싱 (한글 인코딩 이슈 대응)
        request_data = None
        decode_success = False
        
        # UTF-8 우선 시도
        try:
            decoded_text = data.decode('utf-8')
            request_data = json.loads(decoded_text)
            decode_success = True
            print(f"[INFO] UTF-8 디코딩 성공")
        except UnicodeDecodeError:
            print(f"[WARN] UTF-8 디코딩 실패, CP949 시도...")
            # CP949(한국어 윈도우) 시도
            try:
                decoded_text = data.decode('cp949')
                request_data = json.loads(decoded_text)
                decode_success = True
                print(f"[INFO] CP949 디코딩 성공")
            except UnicodeDecodeError:
                print(f"[WARN] CP949 디코딩 실패, latin-1 시도...")
                # latin-1 (모든 바이트를 허용) 시도
                try:
                    decoded_text = data.decode('latin-1')
                    request_data = json.loads(decoded_text)
                    decode_success = True
                    print(f"[INFO] latin-1 디코딩 성공")
                except:
                    pass
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON 파싱 오류: {e}")
        
        # 디코딩 실패 시 오류 응답
        if not decode_success or request_data is None:
            print(f"[ERROR] 모든 인코딩 방식 실패")
            error_response = {
                "protocol": "py_gen_schedule",
                "resp": "fail",
                "data": []
            }
            response = json.dumps(error_response, ensure_ascii=False)
            conn.sendall(response.encode('utf-8'))
            return

        
        # 요청 데이터 저장
        save_request_to_file(request_data, addr)
        
        # 요청 처리 (task 기반 라우팅)
        result = process_request(request_data)
        
        # 응답 데이터 저장 (응답 전에)
        save_response_to_file(result, addr)
        
        # 응답 전송
        response = json.dumps(result, ensure_ascii=False, indent=2)
        conn.sendall(response.encode('utf-8'))
        
        print(f"[INFO] {addr}: 응답 완료 ({result.get('status', 'unknown')})")
        
    except Exception as e:
        print(f"[ERROR] 클라이언트 처리 오류 {addr}: {e}")
        try:
            error_response = {
                "protocol": "py_gen_schedule",
                "resp": "fail",
                "data": []
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