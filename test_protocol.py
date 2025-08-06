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

def test_client_protocol():
    """클라이언트 프로토콜 요청 테스트"""
    
    print("=== 클라이언트 프로토콜 호환성 테스트 ===")
    
    # 클라이언트 형식 요청 (job_category, staff_uid, monthly_workhour 사용)
    client_request = {
        "staff_data": {
            "staff": [
                {"name": "김간호사", "staff_uid": 101, "grade": 3, "grade_name": "일반간호사", "job_category": "간호", "monthly_workhour": 194},
                {"name": "이간호사", "staff_uid": 102, "grade": 4, "grade_name": "간호사", "job_category": "간호", "monthly_workhour": 185},
                {"name": "박간호사", "staff_uid": 103, "grade": 3, "grade_name": "주임간호사", "job_category": "간호", "monthly_workhour": 200},
                {"name": "최간호사", "staff_uid": 104, "grade": 4, "grade_name": "간호사", "job_category": "간호", "monthly_workhour": 190},
                {"name": "정간호사", "staff_uid": 105, "grade": 5, "grade_name": "신규간호사", "job_category": "간호", "monthly_workhour": 175},
                {"name": "장간호사", "staff_uid": 106, "grade": 4, "grade_name": "간호사", "job_category": "간호", "monthly_workhour": 195},
                {"name": "윤간호사", "staff_uid": 107, "grade": 3, "grade_name": "주임간호사", "job_category": "간호", "monthly_workhour": 185},
                {"name": "조간호사", "staff_uid": 108, "grade": 4, "grade_name": "간호사", "job_category": "간호", "monthly_workhour": 190},
                {"name": "한간호사", "staff_uid": 109, "grade": 5, "grade_name": "신규간호사", "job_category": "간호", "monthly_workhour": 180},
                {"name": "강간호사", "staff_uid": 110, "grade": 3, "grade_name": "주임간호사", "job_category": "간호", "monthly_workhour": 205}
            ]
        },
        "shift_type": 3,
        "position": "간호",
        "target_month": "2025-08",
        "custom_rules": {
            "shifts": ["D", "E", "N", "O"],
            "shift_hours": {"D": 8, "E": 8, "N": 8, "O": 0}
        }
    }
    
    print("요청 데이터 (클라이언트 형식):")
    print(f"- 직원 수: {len(client_request['staff_data']['staff'])}명")
    print(f"- 필드: job_category, staff_uid, monthly_workhour")
    print(f"- 직군: {client_request['position']}")
    print(f"- 시프트: {client_request['custom_rules']['shifts']}")
    
    response = send_request(client_request)
    
    if response:
        if response.get("status") == "ok":
            print("✅ 성공: 클라이언트 프로토콜 정상 처리됨")
            
            # 신규간호사 야간 근무 확인
            schedule = response["schedule"]
            newbie_night_count = 0
            
            for date_str, day_schedule in schedule.items():
                for shift_info in day_schedule:
                    if shift_info["shift"] == "N":  # 야간 시프트
                        for person in shift_info["people"]:
                            if person["이름"] in ["정간호사", "한간호사"]:  # 신규간호사
                                newbie_night_count += 1
            
            if newbie_night_count == 0:
                print("✅ 신규간호사 야간 근무 금지 제약 정상 작동")
            else:
                print(f"❌ 신규간호사 야간 근무 {newbie_night_count}회 발견")
                
        elif response.get("result") == "생성실패":
            print("❌ 실패")
            print(f"📝 사유: {response.get('reason', '알 수 없는 오류')}")
            if "details" in response:
                details = response["details"]
                print("🔍 상세정보:")
                print(f"  - 솔버 상태: {details.get('solver_status', 'unknown')}")
                print(f"  - 처리 시간: {details.get('solve_time', 'unknown')}")
                print(f"  - 직원 수: {details.get('staff_count', 'unknown')}")
                if "identified_issues" in details:
                    print(f"  - 식별된 문제: {details['identified_issues']}")
        else:
            print("🚨 예상치 못한 응답 형식")
            print(response)
    else:
        print("🚨 서버 응답 없음")

if __name__ == "__main__":
    print("프로토콜 호환성 및 개선된 오류 메시지 테스트")
    test_client_protocol()