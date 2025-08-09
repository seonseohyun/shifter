#!/usr/bin/env python3
"""
규모별 교대 시스템 형평성 테스트
- 10명 3교대 시스템
- 15명 4교대 시스템  
- 20명 5교대 시스템
"""

import socket
import struct
import json
import time
from typing import Dict, Any, Optional, List
from analyze_fairness import analyze_schedule_fairness
import glob

class ScaleFairnessTestClient:
    def __init__(self, host: str = "localhost", port: int = 6004):
        self.host = host
        self.port = port
    
    def send_request(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """서버에 근무표 생성 요청을 보냅니다."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port))
                
                # JSON 직렬화
                json_data = json.dumps(request_data, ensure_ascii=False)
                json_bytes = json_data.encode('utf-8')
                
                # 리틀엔디안 헤더 생성
                total_size = len(json_bytes)
                header = struct.pack('<II', total_size, total_size)
                
                # 요청 전송
                sock.send(header + json_bytes)
                
                # 응답 헤더 수신
                response_header = sock.recv(8)
                if len(response_header) < 8:
                    return None
                
                total_size, json_size = struct.unpack('<II', response_header)
                
                # 응답 본문 수신
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
    
    # 직급 분포 (실제적인 분포로 설정)
    grades = []
    if count <= 10:
        grades = [3] * (count // 2) + [2] * (count // 3) + [1] * (count - count//2 - count//3)
    elif count <= 15:
        grades = [3] * (count // 3) + [2] * (count // 2) + [1] * (count - count//3 - count//2)
    else:
        grades = [3] * (count // 4) + [2] * (count // 2) + [1] * (count - count//4 - count//2)
    
    # 부족한 경우 1급으로 채움
    while len(grades) < count:
        grades.append(1)
    
    names = [
        "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
        "한", "오", "서", "신", "권", "황", "안", "송", "류", "전"
    ]
    
    for i in range(count):
        staff_data.append({
            "staff_id": 2000 + i + 1,  # 2001부터 시작
            "name": f"{names[i % len(names)]}{position}사{i+1}",
            "grade": grades[i],
            "total_hours": 209 if position == "간호" else 192,
            "position": position
        })
    
    return staff_data

def test_3_shift_system():
    """10명 3교대 시스템 테스트"""
    print("\n🔄 테스트 1: 10명 3교대 시스템 (간호)")
    print("=" * 50)
    
    client = ScaleFairnessTestClient()
    
    # 10명 간호 직원 3교대 시스템
    staff_data = generate_staff_data(10, "간호")
    
    request = {
        "protocol": "py_gen_timetable",
        "data": {
            "staff_data": {
                "staff": staff_data
            },
            "position": "간호",
            "target_month": "2025-07",  # 31일로 테스트
            "custom_rules": {
                "shifts": ["Day", "Evening", "Night", "Off"],
                "shift_hours": {"Day": 8, "Evening": 8, "Night": 8, "Off": 0},
                "night_shifts": ["Night"],
                "off_shifts": ["Off"]
            }
        }
    }
    
    response = client.send_request(request)
    
    if response and response.get("resp") == "success":
        print("✅ 10명 3교대 근무표 생성 성공")
        print(f"📊 생성된 항목 수: {len(response.get('data', []))}")
        
        # 형평성 분석
        schedule_files = glob.glob("data/schedule_response_*.json")
        if schedule_files:
            latest_file = max(schedule_files)
            analyze_schedule_fairness(latest_file)
    else:
        print("❌ 10명 3교대 근무표 생성 실패")

def test_4_shift_system():
    """15명 4교대 시스템 테스트"""
    print("\n🔄 테스트 2: 15명 4교대 시스템 (간호)")
    print("=" * 50)
    
    client = ScaleFairnessTestClient()
    
    # 15명 간호 직원 4교대 시스템 (Early, Day, Evening, Night)
    staff_data = generate_staff_data(15, "간호")
    
    request = {
        "protocol": "py_gen_timetable",
        "data": {
            "staff_data": {
                "staff": staff_data
            },
            "position": "간호",
            "target_month": "2025-08",  # 31일로 테스트
            "custom_rules": {
                "shifts": ["Early", "Day", "Evening", "Night", "Off"],
                "shift_hours": {"Early": 8, "Day": 8, "Evening": 8, "Night": 8, "Off": 0},
                "night_shifts": ["Night"],
                "off_shifts": ["Off"]
            }
        }
    }
    
    response = client.send_request(request)
    
    if response and response.get("resp") == "success":
        print("✅ 15명 4교대 근무표 생성 성공")
        print(f"📊 생성된 항목 수: {len(response.get('data', []))}")
        
        # 형평성 분석
        schedule_files = glob.glob("data/schedule_response_*.json")
        if schedule_files:
            latest_file = max(schedule_files)
            analyze_schedule_fairness(latest_file)
    else:
        print("❌ 15명 4교대 근무표 생성 실패")

def test_5_shift_system():
    """20명 5교대 시스템 테스트"""
    print("\n🔄 테스트 3: 20명 5교대 시스템 (간호)")
    print("=" * 50)
    
    client = ScaleFairnessTestClient()
    
    # 20명 간호 직원 5교대 시스템
    staff_data = generate_staff_data(20, "간호")
    
    request = {
        "protocol": "py_gen_timetable",
        "data": {
            "staff_data": {
                "staff": staff_data
            },
            "position": "간호",
            "target_month": "2025-09",  # 30일로 테스트
            "custom_rules": {
                "shifts": ["Early", "Day", "Late", "Evening", "Night", "Off"],
                "shift_hours": {"Early": 8, "Day": 8, "Late": 8, "Evening": 8, "Night": 8, "Off": 0},
                "night_shifts": ["Night"],
                "off_shifts": ["Off"]
            }
        }
    }
    
    response = client.send_request(request)
    
    if response and response.get("resp") == "success":
        print("✅ 20명 5교대 근무표 생성 성공")
        print(f"📊 생성된 항목 수: {len(response.get('data', []))}")
        
        # 형평성 분석
        schedule_files = glob.glob("data/schedule_response_*.json")
        if schedule_files:
            latest_file = max(schedule_files)
            analyze_schedule_fairness(latest_file)
    else:
        print("❌ 20명 5교대 근무표 생성 실패")

def run_scale_tests():
    """모든 규모 테스트 실행"""
    print("🧪 규모별 교대 시스템 형평성 테스트")
    print("=" * 60)
    print("📋 테스트 시나리오:")
    print("  1️⃣ 10명 3교대 시스템 (Day, Evening, Night)")
    print("  2️⃣ 15명 4교대 시스템 (Early, Day, Evening, Night)")
    print("  3️⃣ 20명 5교대 시스템 (Early, Day, Late, Evening, Night)")
    print("=" * 60)
    
    # 각 테스트 실행
    test_3_shift_system()
    time.sleep(1)
    
    test_4_shift_system()
    time.sleep(1)
    
    test_5_shift_system()
    
    print("\n" + "=" * 60)
    print("🎯 규모별 테스트 완료")
    print("\n📈 예상 형평성 결과:")
    print("  • 10명 시스템: 더 많은 근무 부담, 적은 휴무일")
    print("  • 15명 시스템: 균형잡힌 근무 분배")
    print("  • 20명 시스템: 더 적은 근무 부담, 많은 휴무일")
    print("  • 모든 시스템에서 편차 ≤3일로 형평성 유지 예상")

if __name__ == "__main__":
    run_scale_tests()