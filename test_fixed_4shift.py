#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import json
import time
import random
import os

HOST = '127.0.0.1'
PORT = 6002

def generate_random_staff(count=15):
    """임의의 직원 정보 생성"""
    first_names = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"]
    last_names = ["민수", "영희", "철수", "영수", "정희", "현우", "지영", "승호", "미영", "태현"]
    
    grade_distribution = {
        1: ("수간호사", 1),      # 1명
        2: ("주임간호사", 2),    # 2명  
        3: ("일반간호사", 8),    # 8명
        4: ("간호사", 2),        # 2명
        5: ("신규간호사", 2)     # 2명
    }
    
    staff = []
    staff_id = 2000
    
    for grade, (grade_name, num_count) in grade_distribution.items():
        for i in range(num_count):
            name = random.choice(first_names) + random.choice(last_names)
            work_hours = random.randint(180, 210)  # 180-210시간 범위
            
            staff.append({
                "name": name,
                "staff_id": staff_id,
                "grade": grade,
                "grade_name": grade_name,
                "position": "간호",
                "total_monthly_work_hours": work_hours
            })
            staff_id += 1
    
    return staff

def send_request(request_data):
    """TCP 소켓을 통해 서버에 요청을 보내고 응답을 받음"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            
            start_time = time.time()
            
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
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            response_str = response_data.decode('utf-8')
            return json.loads(response_str), generation_time
    
    except Exception as e:
        print(f"[ERROR] 서버 연결 또는 요청 처리 중 오류: {e}")
        return None, 0

def test_fixed_4shift():
    """수정된 4교대 시스템 테스트"""
    
    staff_data = generate_random_staff(15)
    
    # 수정된 4교대 시나리오들 (더 현실적인 조건)
    test_scenarios = [
        {
            "name": "4교대_수정1_8시간",
            "shifts": ["아침", "오후", "저녁", "밤", "휴무"],
            "shift_hours": {"아침": 8, "오후": 8, "저녁": 8, "밤": 8, "휴무": 0},
            "description": "4교대 8시간 (각 시프트별 인원 배치)"
        },
        {
            "name": "4교대_수정2_7시간",
            "shifts": ["Morning", "Day", "Evening", "Night", "Off"],
            "shift_hours": {"Morning": 7, "Day": 7, "Evening": 7, "Night": 7, "Off": 0},
            "description": "4교대 7시간 (하루 28시간 가능)"
        },
        {
            "name": "4교대_수정3_혼합",
            "shifts": ["Early", "Mid", "Late", "Night", "Rest"],
            "shift_hours": {"Early": 6, "Mid": 8, "Late": 6, "Night": 8, "Rest": 0},
            "description": "4교대 혼합시간 (하루 28시간 가능)"
        },
        {
            "name": "간소화_3교대_대안",
            "shifts": ["Day", "Evening", "Night", "Off"],
            "shift_hours": {"Day": 8, "Evening": 8, "Night": 8, "Off": 0},
            "description": "3교대 대안 (검증된 패턴)"
        },
        {
            "name": "2교대_대안",
            "shifts": ["LongDay", "LongNight", "Off"],
            "shift_hours": {"LongDay": 12, "LongNight": 12, "Off": 0},
            "description": "2교대 대안 (검증된 패턴)"
        }
    ]
    
    print("=== 수정된 4교대 시스템 테스트 ===")
    print("목표: 실패했던 4교대 시스템 해결 방안 검증")
    
    success_count = 0
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*50}")
        print(f"테스트 {i}: {scenario['name']}")
        print(f"{'='*50}")
        print(f"설명: {scenario['description']}")
        print(f"시프트: {scenario['shifts']}")
        print(f"시간: {scenario['shift_hours']}")
        
        # 수학적 검증
        non_off_shifts = [s for s in scenario['shifts'] if scenario['shift_hours'][s] > 0]
        max_daily_hours = sum(scenario['shift_hours'][s] for s in non_off_shifts)
        avg_target = sum(staff["total_monthly_work_hours"] for staff in staff_data) / len(staff_data)
        
        print(f"수학적 검증:")
        print(f"  - 근무 시프트 수: {len(non_off_shifts)}개")
        print(f"  - 하루 최대 시간: {max_daily_hours}시간")
        print(f"  - 평균 목표시간: {avg_target:.1f}시간")
        
        request = {
            "position": "간호",
            "shift_type": 3,
            "target_month": "2025-09",
            "staff_data": {
                "staff": staff_data
            },
            "custom_rules": {
                "shifts": scenario["shifts"],
                "shift_hours": scenario["shift_hours"]
            }
        }
        
        response, generation_time = send_request(request)
        
        if response and response.get("status") == "ok":
            success_count += 1
            print(f"✅ 성공 - {generation_time:.2f}초")
            
            # 결과 저장
            os.makedirs("./client_data", exist_ok=True)
            output_file = f"./client_data/fixed_4shift_test_{i}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(response["schedule"], f, ensure_ascii=False, indent=2)
            print(f"📁 저장: {output_file}")
            
        else:
            print(f"❌ 실패 - {response if response else '응답 없음'}")
        
        time.sleep(0.1)
    
    print(f"\n{'='*50}")
    print(f"수정된 4교대 테스트 결과")
    print(f"{'='*50}")
    print(f"성공: {success_count}/{len(test_scenarios)} ({success_count/len(test_scenarios)*100:.1f}%)")
    
    if success_count > 0:
        print(f"\n💡 성공한 패턴 분석:")
        if success_count == len(test_scenarios):
            print("   - 모든 수정안이 성공!")
        print("   - 시간 배정 증가 (6시간 → 7-8시간)")
        print("   - 하루 최대 시간 확보 (28-32시간 가능)")
    
    return success_count, len(test_scenarios)

if __name__ == "__main__":
    print("4교대 시스템 수정안 테스트 클라이언트")
    print("서버가 실행 중인지 확인하세요 (포트 6002)")
    
    success, total = test_fixed_4shift()
    
    if success == total:
        print(f"\n🎉 모든 수정안 성공! ({success}/{total})")
    else:
        print(f"\n⚠️  일부 수정안 실패 ({success}/{total})")
    
    print("테스트 완료")