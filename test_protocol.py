#!/usr/bin/env python3
import socket
import json

def test_protocol():
    # 간단한 테스트 요청
    test_request = {
        "protocol": "py_gen_timetable",
        "data": {
            "staff_data": {
                "staff": [
                    {
                        "name": "테스트간호사",
                        "staff_id": 9999,
                        "grade": 3,
                        "total_monthly_work_hours": 195
                    }
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
    
    # 서버 연결
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 6004))
    
    # 요청 전송
    request_json = json.dumps(test_request, ensure_ascii=False)
    print("=== 전송 요청 ===")
    print(json.dumps(test_request, ensure_ascii=False, indent=2))
    
    sock.sendall(request_json.encode('utf-8'))
    sock.shutdown(socket.SHUT_WR)
    
    # 응답 수신
    response_data = b''
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response_data += chunk
    
    sock.close()
    
    # 응답 출력
    print("\n=== 서버 응답 ===")
    response_str = response_data.decode('utf-8')
    print("Raw 응답:")
    print(response_str)
    
    try:
        response_json = json.loads(response_str)
        print("\nJSON 파싱된 응답:")
        print(json.dumps(response_json, ensure_ascii=False, indent=2))
        
        # 프로토콜 확인
        if "protocol" in response_json:
            print(f"\n✅ 프로토콜 필드 존재: {response_json['protocol']}")
        else:
            print(f"\n❌ 프로토콜 필드 없음")
            print(f"응답 키들: {list(response_json.keys())}")
            
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 실패: {e}")

if __name__ == "__main__":
    test_protocol()