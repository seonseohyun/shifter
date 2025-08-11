#!/usr/bin/env python3
"""
7월 (31일) 형평성 테스트 - 이전에 문제가 되었던 7월 31일에 대한 형평성 테스트
"""

import socket
import struct
import json
from typing import Dict, Any, Optional

def send_schedule_request(request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """서버에 근무표 생성 요청을 보냅니다."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(("localhost", 6004))
            
            # JSON 직렬화
            json_data = json.dumps({"protocol": "py_gen_timetable", **request_data}, ensure_ascii=False)
            json_bytes = json_data.encode('utf-8')
            
            # 리틀엔디안 헤더 생성
            total_size = len(json_bytes)
            header = struct.pack('<II', total_size, total_size)
            
            # 요청 전송
            sock.send(header + json_bytes)
            
            # 응답 수신
            response_header = sock.recv(8)
            total_size, json_size = struct.unpack('<II', response_header)
            
            response_data = b""
            while len(response_data) < json_size:
                chunk = sock.recv(json_size - len(response_data))
                if not chunk:
                    break
                response_data += chunk
                
            return json.loads(response_data.decode('utf-8'))
            
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return None

def test_july_fairness():
    """7월 31일에 대한 형평성 테스트"""
    
    print("🧪 7월 (31일) 형평성 테스트")
    print("=" * 50)
    print("🎯 목표: 이전 문제 (uid1=21일 휴무) 해결 확인")
    print()
    
    # 7월 테스트 데이터 (이전 문제가 발생했던 동일한 조건)
    july_request = {
        "year": 2025,
        "month": 7,  # 31일
        "staff": [
            {"staff_id": 1001, "name": "김간호사", "grade": 3, "total_hours": 209, "position": "간호"},
            {"staff_id": 1002, "name": "이간호사", "grade": 3, "total_hours": 209, "position": "간호"},
            {"staff_id": 1003, "name": "박간호사", "grade": 2, "total_hours": 209, "position": "간호"},
            {"staff_id": 1004, "name": "최간호사", "grade": 2, "total_hours": 209, "position": "간호"},
            {"staff_id": 1005, "name": "정간호사", "grade": 1, "total_hours": 209, "position": "간호"}
        ]
    }
    
    response = send_schedule_request(july_request)
    
    if response and response.get("resp") == "success":
        print("✅ 7월 근무표 생성 성공!")
        
        # 직원별 휴무일 카운트
        staff_off_days = {staff["staff_id"]: 0 for staff in july_request["staff"]}
        staff_names = {staff["staff_id"]: staff["name"] for staff in july_request["staff"]}
        
        for entry in response.get("data", []):
            if entry["shift"] == "Off":
                for person in entry["people"]:
                    staff_off_days[person["staff_id"]] += 1
        
        print("\n📊 7월 휴무일 분석:")
        print("-" * 30)
        
        for staff_id, off_days in staff_off_days.items():
            name = staff_names[staff_id]
            percentage = (off_days / 31) * 100
            print(f"👤 {name} (uid{staff_id}): {off_days}일 ({percentage:.1f}%)")
            
            if staff_id == 1001:  # 이전에 문제가 되었던 uid1
                if off_days <= 12:  # 간호 직원 최대 휴무일
                    print("   ✅ 개선됨! 이전(21일) → 현재({off_days}일)")
                else:
                    print(f"   ❌ 여전히 문제: {off_days}일")
        
        # 형평성 평가
        off_days_list = list(staff_off_days.values())
        min_off = min(off_days_list)
        max_off = max(off_days_list)
        avg_off = sum(off_days_list) / len(off_days_list)
        
        print(f"\n📈 형평성 요약:")
        print(f"   최소 휴무일: {min_off}일")
        print(f"   최대 휴무일: {max_off}일")
        print(f"   평균 휴무일: {avg_off:.1f}일")
        print(f"   편차 범위: {max_off - min_off}일")
        
        if max_off - min_off <= 3:
            print("   ✅ 형평성: 매우 양호!")
            print("   🎉 이전 문제(21일 vs 다른 직원) 완전 해결!")
        else:
            print(f"   ⚠️ 형평성: 개선 필요 (편차 {max_off - min_off}일)")
            
    else:
        print("❌ 7월 근무표 생성 실패")

if __name__ == "__main__":
    test_july_fairness()