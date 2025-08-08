#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
근무표 생성 프로토콜 테스트 (py_gen_timetable → py_gen_schedule)
"""

import socket
import json
import struct


def test_schedule_protocol():
    """py_gen_timetable 프로토콜로 근무표 생성 요청 테스트"""
    
    print("🔧 근무표 생성 프로토콜 테스트")
    print("=" * 60)
    
    # py_gen_timetable 프로토콜 요청
    schedule_request = {
        "protocol": "py_gen_timetable",
        "data": {
            "staff_data": {
                "staff": [
                    {
                        "name": "김간호사",
                        "staff_id": 1001,
                        "grade": 3,
                        "total_hours": 160
                    },
                    {
                        "name": "이간호사", 
                        "staff_id": 1002,
                        "grade": 3,
                        "total_hours": 160
                    },
                    {
                        "name": "박간호사",
                        "staff_id": 1003,
                        "grade": 2,
                        "total_hours": 160
                    },
                    {
                        "name": "최간호사",
                        "staff_id": 1004,
                        "grade": 2,
                        "total_hours": 160
                    },
                    {
                        "name": "정간호사",
                        "staff_id": 1005,
                        "grade": 1,
                        "total_hours": 160
                    }
                ]
            },
            "position": "간호",
            "target_month": "2025-09",
            "custom_rules": {
                "shifts": ["Day", "Evening", "Night", "Off"],
                "shift_hours": {
                    "Day": 8,
                    "Evening": 8, 
                    "Night": 8,
                    "Off": 0
                },
                "night_shifts": ["Night"],
                "off_shifts": ["Off"]
            }
        }
    }
    
    try:
        # JSON 인코딩
        json_str = json.dumps(schedule_request, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')
        
        total_size = len(json_bytes)
        json_size = len(json_bytes)
        
        # 리틀엔디안 헤더 생성 (C++ uint32_t 호환)
        header = struct.pack('<I', total_size) + struct.pack('<I', json_size)
        
        print(f"📤 요청 전송:")
        print(f"  - 프로토콜: py_gen_timetable")
        print(f"  - JSON 길이: {len(json_bytes)} 바이트")
        print(f"  - 헤더: totalSize={total_size}, jsonSize={json_size}")
        print(f"  - 직원 수: 3명")
        print(f"  - 대상 월: 2025-09")
        
        # 서버 연결
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(('127.0.0.1', 6004))
            
            # 헤더 + 데이터 전송
            sock.sendall(header + json_bytes)
            print("  ✅ 요청 전송 완료")
            
            # 응답 헤더 수신
            response_header = recv_exact(sock, 8)
            resp_total_size = struct.unpack('<I', response_header[:4])[0]
            resp_json_size = struct.unpack('<I', response_header[4:8])[0]
            
            print(f"\n📥 응답 수신:")
            print(f"  - 응답 헤더: totalSize={resp_total_size}, jsonSize={resp_json_size}")
            
            # 응답 데이터 수신
            response_data = recv_exact(sock, resp_json_size)
            response_json = response_data.decode('utf-8')
            response = json.loads(response_json)
            
            print(f"  - 응답 길이: {len(response_data)} 바이트")
            print(f"  ✅ 응답 수신 완료")
            
            # 결과 출력
            print(f"\n🎯 근무표 생성 응답 분석:")
            print("-" * 40)
            print(f"응답 프로토콜: {response.get('protocol', 'N/A')}")
            print(f"응답 상태: {response.get('resp', 'N/A')}")
            
            if response.get("resp") == "success":
                schedule_data = response.get("data", [])
                print(f"✅ 성공!")
                print(f"생성된 근무표 항목 수: {len(schedule_data)}")
                print("첫 3개 항목:")
                for i, entry in enumerate(schedule_data[:3]):
                    date = entry.get("date", "N/A")
                    shift = entry.get("shift", "N/A") 
                    people_count = len(entry.get("people", []))
                    print(f"  - {date}: {shift} 근무 ({people_count}명)")
            else:
                print(f"❌ 실패")
                if "error" in response:
                    print(f"오류: {response.get('error', 'Unknown error')}")
            print("-" * 40)
            
            return response.get("resp") == "success"
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


def recv_exact(sock, n):
    """정확히 n바이트 수신"""
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("연결이 종료됨")
        buf += chunk
    return buf


if __name__ == "__main__":
    print("🚀 근무표 생성 프로토콜 테스트")
    print("서버가 실행 중인지 확인: python3 shift_server_optimized.py")
    print()
    
    success = test_schedule_protocol()
    
    if success:
        print("\n✨ 테스트 성공! 근무표 생성 프로토콜 정상 작동")
        print("🔄 프로토콜 형식:")
        print("  - 요청: py_gen_timetable")
        print("  - 응답: py_gen_schedule") 
        print("  - 구조: protocol, resp, data가 최상위 레벨")
        print("  - 헤더: 리틀엔디안 바이너리")
    else:
        print("\n💥 테스트 실패! 프로토콜 호환성 문제 있음")