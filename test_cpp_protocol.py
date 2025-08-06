#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C++ 프로토콜 호환성 테스트
변경이 필요한부분.txt의 프로토콜 형식 검증
"""

import socket
import json

HOST = '127.0.0.1'
PORT = 6004

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

def test_cpp_protocol():
    """C++ 프로토콜 형식 테스트"""
    
    print("=== C++ 프로토콜 호환성 테스트 ===")
    
    # C++ 프로토콜 형식 (data 래퍼 포함)
    cpp_request = {
        "protocol": "gen_schedule",
        "data": {
            "staff_data": {
                "staff": [
                    {"name": "김간호사", "staff_id": 1001, "grade": 3, "position": "간호", "total_monthly_work_hours": 195},
                    {"name": "이간호사", "staff_id": 1002, "grade": 4, "position": "간호", "total_monthly_work_hours": 190},
                    {"name": "박간호사", "staff_id": 1003, "grade": 5, "position": "간호", "total_monthly_work_hours": 180},
                    {"name": "최간호사", "staff_id": 1004, "grade": 3, "position": "간호", "total_monthly_work_hours": 200}
                ]
            },
            "position": "간호",
            "target_month": "2025-09",
            "custom_rules": {
                "shifts": ["Day", "Evening", "Night", "Off"],
                "shift_hours": {"Day": 8, "Evening": 8, "Night": 8, "Off": 0},
                "night_shifts": ["Night"],
                "off_shifts": ["Off"]
            }
        }
    }
    
    print("C++ 프로토콜 요청 전송 중...")
    response = send_request(cpp_request)
    
    if response:
        print("✅ 서버 응답 수신 성공")
        
        # 프로토콜 필드 확인
        if "protocol" in response:
            print(f"📡 응답 프로토콜: {response['protocol']}")
            
            if response["protocol"] == "py_gen_schedule":
                print("✅ C++ 프로토콜 응답 형식 정확")
            else:
                print(f"❌ 예상된 프로토콜: py_gen_schedule, 실제: {response['protocol']}")
        else:
            print("❌ 응답에 protocol 필드가 없음")
        
        # 응답 상태 확인
        if response.get("status") == "ok":
            print("✅ 스케줄 생성 성공")
            print(f"📊 처리 시간: {response.get('details', {}).get('solve_time', 'unknown')}")
            print(f"📊 직원 수: {response.get('details', {}).get('staff_count', 'unknown')}")
            
            # 시프트 식별 확인
            shifts_identified = response.get('details', {}).get('shifts_identified', {})
            print(f"🔍 식별된 야간 시프트: {shifts_identified.get('night_shifts', [])}")
            print(f"🔍 식별된 휴무 시프트: {shifts_identified.get('off_shifts', [])}")
            
        else:
            print(f"❌ 스케줄 생성 실패: {response.get('reason', 'unknown')}")
            
    else:
        print("🚨 서버 응답 없음")

def test_python_protocol():
    """Python 프로토콜 형식 테스트 (기존 방식)"""
    
    print(f"\n=== Python 프로토콜 테스트 (기존 방식) ===")
    
    # Python 프로토콜 형식 (직접 데이터)
    python_request = {
        "staff_data": {
            "staff": [
                {"name": "소방관A", "staff_id": 2001, "grade": 3, "position": "소방", "total_monthly_work_hours": 185},
                {"name": "소방관B", "staff_id": 2002, "grade": 4, "position": "소방", "total_monthly_work_hours": 180},
                {"name": "소방관C", "staff_id": 2003, "grade": 5, "position": "소방", "total_monthly_work_hours": 175}
            ]
        },
        "position": "소방",
        "target_month": "2025-09",
        "custom_rules": {
            "shifts": ["D24", "O"],
            "shift_hours": {"D24": 24, "O": 0},
            "night_shifts": ["D24"],
            "off_shifts": ["O"]
        }
    }
    
    print("Python 프로토콜 요청 전송 중...")
    response = send_request(python_request)
    
    if response:
        print("✅ 서버 응답 수신 성공")
        
        # 프로토콜 필드 확인 (없어야 정상)
        if "protocol" in response:
            print(f"❌ 예상치 못한 protocol 필드: {response['protocol']}")
        else:
            print("✅ Python 프로토콜 응답 형식 정확 (protocol 필드 없음)")
        
        # 응답 상태 확인
        if response.get("status") == "ok":
            print("✅ 소방 스케줄 생성 성공")
            print(f"📊 처리 시간: {response.get('details', {}).get('solve_time', 'unknown')}")
            
            # 소방 제약 확인
            print("🔥 소방 직군 제약조건 테스트")
            
        elif response.get("result") == "생성실패":
            print(f"❌ 소방 스케줄 생성 실패: {response.get('reason', 'unknown')}")
            
            # 상세 분석 확인
            details = response.get('details', {})
            if 'identified_issues' in details:
                print(f"🔍 문제점: {details['identified_issues']}")
            if 'suggestions' in details:
                print(f"💡 해결방안: {details['suggestions']}")
            
    else:
        print("🚨 서버 응답 없음")

def test_invalid_protocol():
    """잘못된 요청 테스트"""
    
    print(f"\n=== 잘못된 요청 테스트 ===")
    
    # 잘못된 요청 (staff 데이터 없음)
    invalid_request = {
        "protocol": "gen_schedule",
        "data": {
            "position": "간호",
            "target_month": "2025-09"
            # staff_data 누락
        }
    }
    
    print("잘못된 요청 전송 중...")
    response = send_request(invalid_request)
    
    if response:
        print("✅ 서버 응답 수신 성공")
        
        # 오류 응답 확인
        if response.get("status") == "error":
            print("✅ 오류 응답 정상")
            print(f"📝 오류 사유: {response.get('reason', 'unknown')}")
            
            # C++ 프로토콜 오류 응답 확인
            if "protocol" in response and response["protocol"] == "py_gen_schedule":
                print("✅ C++ 프로토콜 오류 응답 형식 정확")
            else:
                print("❌ C++ 프로토콜 오류 응답 형식 문제")
                
        else:
            print("❌ 오류가 있는 요청인데 성공 응답")
            
    else:
        print("🚨 서버 응답 없음")

if __name__ == "__main__":
    print("시프트 스케줄러 v2.0 C++ 프로토콜 호환성 테스트")
    
    test_cpp_protocol()
    test_python_protocol()
    test_invalid_protocol()
    
    print("\n테스트 완료")