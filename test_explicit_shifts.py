#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
명시적 시프트 지정 시스템 테스트
v2.0 서버의 핵심 기능 검증
"""

import socket
import json

HOST = '127.0.0.1'
PORT = 6002

def send_request(request_data):
    """TCP 소켓을 통해 서버에 요청을 보내고 응답을 받음"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            
            request_json = json.dumps(request_data, ensure_ascii=False)
            s.sendall(request_json.encode('utf-8'))
            s.shutdown(socket.SHUT_WR)
            
            # 응답 수신
            response_data = b''
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            response_str = response_data.decode('utf-8')
            return json.loads(response_str)
    
    except Exception as e:
        print(f"[ERROR] 서버 연결 또는 요청 처리 중 오류: {e}")
        return None

def test_explicit_shift_specification():
    """명시적 시프트 지정 시스템 테스트"""
    
    print("=== 명시적 시프트 지정 시스템 테스트 ===")
    
    # 기본 직원 데이터
    staff_data = {
        "staff": [
            {"name": "김간호사", "staff_id": 1001, "grade": 3, "grade_name": "주임간호사", "position": "간호", "total_monthly_work_hours": 195},
            {"name": "이간호사", "staff_id": 1002, "grade": 4, "grade_name": "간호사", "position": "간호", "total_monthly_work_hours": 190},
            {"name": "박간호사", "staff_id": 1003, "grade": 4, "grade_name": "간호사", "position": "간호", "total_monthly_work_hours": 188},
            {"name": "최간호사", "staff_id": 1004, "grade": 3, "grade_name": "주임간호사", "position": "간호", "total_monthly_work_hours": 200},
            {"name": "정간호사", "staff_id": 1005, "grade": 5, "grade_name": "신규간호사", "position": "간호", "total_monthly_work_hours": 175}
        ]
    }
    
    test_scenarios = [
        {
            "name": "케이스 1: 명시적 야간/휴무 지정 (영문)",
            "custom_rules": {
                "shifts": ["Day", "Evening", "Night", "Off"],
                "shift_hours": {"Day": 8, "Evening": 8, "Night": 8, "Off": 0},
                "night_shifts": ["Night"],  # 명시적 지정
                "off_shifts": ["Off"]       # 명시적 지정
            },
            "expected_night": ["Night"],
            "expected_off": ["Off"]
        },
        {
            "name": "케이스 2: 명시적 야간/휴무 지정 (한글)",
            "custom_rules": {
                "shifts": ["주간", "오후", "야간", "휴무"],
                "shift_hours": {"주간": 8, "오후": 8, "야간": 8, "휴무": 0},
                "night_shifts": ["야간"],   # 명시적 지정
                "off_shifts": ["휴무"]      # 명시적 지정
            },
            "expected_night": ["야간"],
            "expected_off": ["휴무"]
        },
        {
            "name": "케이스 3: 문제가 있던 Morning 시프트 (자동 감지)",
            "custom_rules": {
                "shifts": ["Morning", "Afternoon", "Night", "Rest"],
                "shift_hours": {"Morning": 8, "Afternoon": 8, "Night": 8, "Rest": 0}
                # night_shifts, off_shifts 미지정 → 자동 감지
            },
            "expected_night": ["Night"],   # 자동 감지 예상
            "expected_off": ["Rest"]       # 자동 감지 예상
        },
        {
            "name": "케이스 4: 복합 야간 시프트 명시",
            "custom_rules": {
                "shifts": ["D", "E", "N1", "N2", "O"],
                "shift_hours": {"D": 8, "E": 8, "N1": 8, "N2": 8, "O": 0},
                "night_shifts": ["N1", "N2"],  # 복수 야간 명시
                "off_shifts": ["O"]
            },
            "expected_night": ["N1", "N2"],
            "expected_off": ["O"]
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"테스트 {i}: {scenario['name']}")
        print(f"시프트: {scenario['custom_rules']['shifts']}")
        if "night_shifts" in scenario["custom_rules"]:
            print(f"명시적 야간: {scenario['custom_rules']['night_shifts']}")
        if "off_shifts" in scenario["custom_rules"]:
            print(f"명시적 휴무: {scenario['custom_rules']['off_shifts']}")
        
        request_data = {
            "staff_data": staff_data,
            "position": "간호",
            "target_month": "2025-09",
            "custom_rules": scenario["custom_rules"]
        }
        
        response = send_request(request_data)
        
        if response:
            if response.get("status") == "ok":
                print("✅ 성공: 스케줄 생성 완료")
                
                # 시프트 식별 확인
                details = response.get("details", {})
                shifts_identified = details.get("shifts_identified", {})
                actual_night = shifts_identified.get("night_shifts", [])
                actual_off = shifts_identified.get("off_shifts", [])
                
                print(f"🔍 식별된 시프트:")
                print(f"  - 야간: {actual_night}")
                print(f"  - 휴무: {actual_off}")
                
                # 예상값과 비교
                expected_night = scenario["expected_night"]
                expected_off = scenario["expected_off"]
                
                night_match = set(actual_night) == set(expected_night)
                off_match = set(actual_off) == set(expected_off)
                
                if night_match and off_match:
                    print("✅ 시프트 식별 정확함")
                else:
                    print("❌ 시프트 식별 불일치")
                    if not night_match:
                        print(f"  야간 불일치: 예상 {expected_night} vs 실제 {actual_night}")
                    if not off_match:
                        print(f"  휴무 불일치: 예상 {expected_off} vs 실제 {actual_off}")
                
                # 신규간호사 야간 근무 확인
                schedule = response["schedule"]
                newbie_night_count = 0
                
                for date_str, day_schedule in schedule.items():
                    for shift_info in day_schedule:
                        if shift_info["shift"] in actual_night:
                            for person in shift_info["people"]:
                                if person["이름"] == "정간호사":  # grade 5 신규
                                    newbie_night_count += 1
                
                if newbie_night_count == 0:
                    print("✅ 신규간호사 야간 근무 금지 제약 성공")
                else:
                    print(f"❌ 신규간호사 야간 근무 {newbie_night_count}회 발견")
                
                # 처리 시간 확인
                solve_time = details.get("solve_time", "unknown")
                print(f"⏱️ 처리 시간: {solve_time}")
                
            elif response.get("result") == "생성실패":
                print(f"❌ 생성 실패")
                print(f"📝 사유: {response.get('reason', '알 수 없는 오류')}")
                
                # 상세 분석 정보 출력
                details = response.get("details", {})
                if "analysis" in details:
                    analysis = details["analysis"]
                    print(f"🔍 상세 분석:")
                    basic_info = analysis.get("basic_info", {})
                    print(f"  - 직원: {basic_info.get('staff_count')}명")
                    print(f"  - 근무 시프트: {basic_info.get('work_shifts')}")
                    
                    if "identified_issues" in details:
                        print(f"  - 문제점: {details['identified_issues']}")
            else:
                print("🚨 예상치 못한 응답 형식")
                print(response)
        else:
            print("🚨 서버 응답 없음")

def test_client_protocol_compatibility():
    """클라이언트 프로토콜 호환성 테스트"""
    
    print(f"\n{'='*60}")
    print("클라이언트 프로토콜 호환성 테스트")
    
    # 클라이언트 형식 (job_category, staff_uid, monthly_workhour)
    client_request = {
        "staff_data": {
            "staff": [
                {"name": "김간호사", "staff_uid": 101, "grade": 3, "job_category": "간호", "monthly_workhour": 195},
                {"name": "이간호사", "staff_uid": 102, "grade": 4, "job_category": "간호", "monthly_workhour": 190},
                {"name": "박간호사", "staff_uid": 103, "grade": 5, "job_category": "간호", "monthly_workhour": 180}
            ]
        },
        "position": "간호",
        "target_month": "2025-09",
        "custom_rules": {
            "shifts": ["D", "E", "N", "O"],
            "shift_hours": {"D": 8, "E": 8, "N": 8, "O": 0},
            "night_shifts": ["N"],
            "off_shifts": ["O"]
        }
    }
    
    print("요청 형식: 클라이언트 (job_category, staff_uid, monthly_workhour)")
    
    response = send_request(client_request)
    
    if response and response.get("status") == "ok":
        print("✅ 클라이언트 프로토콜 호환성 성공")
    else:
        print(f"❌ 호환성 실패: {response.get('reason') if response else '응답 없음'}")

if __name__ == "__main__":
    print("시프트 스케줄러 v2.0 테스트 시작")
    test_explicit_shift_specification()
    test_client_protocol_compatibility()
    print("\n테스트 완료")