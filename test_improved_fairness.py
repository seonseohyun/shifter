#!/usr/bin/env python3
"""
개선된 형평성 제약조건 테스트 - 동적 제약조건 적용 후 테스트
"""

import socket
import struct
import json
import time
from typing import Dict, Any, Optional, List
from analyze_fairness import analyze_schedule_fairness
import glob

class ImprovedFairnessTestClient:
    def __init__(self, host: str = "localhost", port: int = 6004):
        self.host = host
        self.port = port
    
    def send_request(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """서버에 근무표 생성 요청을 보냅니다."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port))
                
                json_data = json.dumps(request_data, ensure_ascii=False)
                json_bytes = json_data.encode('utf-8')
                
                total_size = len(json_bytes)
                header = struct.pack('<II', total_size, total_size)
                
                sock.send(header + json_bytes)
                
                response_header = sock.recv(8)
                if len(response_header) < 8:
                    return None
                
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

def generate_staff_data(count: int, position: str = "간호") -> List[Dict[str, Any]]:
    """지정된 수의 직원 데이터를 생성합니다."""
    staff_data = []
    
    names = [
        "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
        "한", "오", "서", "신", "권", "황", "안", "송", "류", "전"
    ]
    
    grades = [3, 3, 2, 2, 1] * (count // 5) + [1] * (count % 5)
    
    for i in range(count):
        staff_data.append({
            "staff_id": 3000 + i + 1,  # 3001부터 시작
            "name": f"{names[i % len(names)]}{position}사{i+1}",
            "grade": grades[i],
            "total_hours": 209 if position == "간호" else 192,
            "position": position
        })
    
    return staff_data

def test_improved_system(staff_count: int, system_name: str, month: int = 7):
    """개선된 형평성 제약조건 테스트"""
    print(f"\n🔧 {system_name}: {staff_count}명 시스템 (개선된 제약조건)")
    print("=" * 60)
    
    client = ImprovedFairnessTestClient()
    staff_data = generate_staff_data(staff_count, "간호")
    
    # 교대 시스템 구성 (직원 수에 따라)
    if staff_count <= 10:
        shifts = ["Day", "Evening", "Night", "Off"]
        shift_hours = {"Day": 8, "Evening": 8, "Night": 8, "Off": 0}
    elif staff_count <= 15:
        shifts = ["Early", "Day", "Evening", "Night", "Off"]
        shift_hours = {"Early": 8, "Day": 8, "Evening": 8, "Night": 8, "Off": 0}
    else:
        shifts = ["Early", "Day", "Late", "Evening", "Night", "Off"]
        shift_hours = {"Early": 8, "Day": 8, "Late": 8, "Evening": 8, "Night": 8, "Off": 0}
    
    request = {
        "protocol": "py_gen_timetable",
        "data": {
            "staff_data": {
                "staff": staff_data
            },
            "position": "간호",
            "target_month": f"2025-{month:02d}",
            "custom_rules": {
                "shifts": shifts,
                "shift_hours": shift_hours,
                "night_shifts": ["Night"],
                "off_shifts": ["Off"]
            }
        }
    }
    
    response = client.send_request(request)
    
    if response and response.get("resp") == "success":
        print(f"✅ {staff_count}명 근무표 생성 성공")
        print(f"📊 생성된 항목 수: {len(response.get('data', []))}")
        
        # 형평성 분석
        schedule_files = glob.glob("data/schedule_response_*.json")
        if schedule_files:
            latest_file = max(schedule_files)
            analyze_schedule_fairness(latest_file)
        
        print(f"\n🎯 {system_name} 동적 제약조건:")
        if staff_count >= 15:
            print("   📉 대규모 시스템: 최대 휴무일 ≤ 8일 (엄격)")
        elif staff_count >= 10:
            print("   📊 중규모 시스템: 최대 휴무일 ≤ 9일 (보통)")
        else:
            print("   📈 소규모 시스템: 최대 휴무일 ≤ 10일 (기본)")
    else:
        print(f"❌ {staff_count}명 근무표 생성 실패")

def run_improved_tests():
    """개선된 형평성 테스트 실행"""
    print("🚀 개선된 형평성 제약조건 테스트")
    print("=" * 60)
    print("🎯 목표: 모든 시스템에서 편차 ≤3일 달성")
    print("🔧 개선사항:")
    print("   • 동적 최대 휴무일 제약 (직원 수별)")
    print("   • 대규모 시스템 엄격 제약 (15명↑: 8일, 10명↑: 9일)")  
    print("   • 최소 근무일 21일로 강화")
    print("=" * 60)
    
    # 각 시스템 테스트
    test_improved_system(10, "중규모 3교대", 7)   # 31일
    time.sleep(1)
    
    test_improved_system(15, "대규모 4교대", 8)   # 31일  
    time.sleep(1)
    
    test_improved_system(20, "대규모 5교대", 9)   # 30일
    
    print("\n" + "=" * 60)
    print("🎉 개선된 형평성 테스트 완료")
    print("\n📈 기대 결과:")
    print("   ✅ 10명 시스템: 편차 ≤3일 (7-9일 휴무)")
    print("   ✅ 15명 시스템: 편차 ≤3일 (6-8일 휴무)")
    print("   ✅ 20명 시스템: 편차 ≤3일 (6-8일 휴무)")

if __name__ == "__main__":
    run_improved_tests()