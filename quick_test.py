#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

def test_dynamic_shifts():
    """동적 시프트 식별 간단 테스트"""
    
    # 기본 직원 데이터 (5명으로 축소)
    staff_data = {
        "staff": [
            {"name": "김간호사", "staff_id": 1001, "grade": 5, "grade_name": "신규간호사", "position": "간호", "total_monthly_work_hours": 185},
            {"name": "이간호사", "staff_id": 1002, "grade": 4, "grade_name": "간호사", "position": "간호", "total_monthly_work_hours": 195},
            {"name": "박간호사", "staff_id": 1003, "grade": 3, "grade_name": "주임간호사", "position": "간호", "total_monthly_work_hours": 188},
            {"name": "최간호사", "staff_id": 1004, "grade": 4, "grade_name": "간호사", "position": "간호", "total_monthly_work_hours": 190},
            {"name": "정간호사", "staff_id": 1005, "grade": 5, "grade_name": "신규간호사", "position": "간호", "total_monthly_work_hours": 180}
        ]
    }
    
    test_scenarios = [
        {
            "name": "영문 Night 시프트",
            "custom_rules": {
                "shifts": ["Day", "Evening", "Night", "Off"], 
                "shift_hours": {"Day": 8, "Evening": 8, "Night": 8, "Off": 0}
            }
        },
        {
            "name": "한글 야간 시프트", 
            "custom_rules": {
                "shifts": ["주간", "오후", "야간", "휴무"],
                "shift_hours": {"주간": 8, "오후": 8, "야간": 8, "휴무": 0}
            }
        },
        {
            "name": "한글 밤 시프트",
            "custom_rules": {
                "shifts": ["새벽", "오전", "밤", "쉼"],
                "shift_hours": {"새벽": 8, "오전": 8, "밤": 8, "쉼": 0}
            }
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n=== 테스트 {i}: {scenario['name']} ===")
        
        request_data = {
            "staff_data": staff_data,
            "position": "간호", 
            "target_month": "2025-09",
            "custom_rules": scenario["custom_rules"]
        }
        
        response = send_request(request_data)
        
        if response and response.get("status") == "ok":
            print("✅ 근무표 생성 성공")
            
            # 신규간호사 야간 근무 확인
            schedule = response["schedule"]
            newbie_night_count = 0
            
            # 예상 야간 시프트 키워드 매칭
            night_keywords = ['night', '야간', '밤']
            night_shifts_in_scenario = [s for s in scenario["custom_rules"]["shifts"] 
                                      if any(nk.lower() in s.lower() for nk in night_keywords)]
            
            print(f"예상 야간 시프트: {night_shifts_in_scenario}")
            
            for date_str, day_schedule in schedule.items():
                for shift_info in day_schedule:
                    shift = shift_info["shift"]
                    if shift in night_shifts_in_scenario:
                        for person in shift_info["people"]:
                            if person["이름"] in ["김간호사", "정간호사"]:  # 신규간호사 (grade 5)
                                newbie_night_count += 1
            
            if newbie_night_count == 0:
                print("✅ 신규간호사 야간 근무 금지 제약 성공")
            else:
                print(f"❌ 신규간호사 야간 근무 {newbie_night_count}회 발견")
                
        elif response and response.get("result") == "생성실패":
            print(f"❌ 생성 실패: {response.get('reason', '알 수 없는 오류')}")
        else:
            print("🚨 응답 없음 또는 오류")

if __name__ == "__main__":
    print("동적 시프트 식별 빠른 테스트")
    test_dynamic_shifts()