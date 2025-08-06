#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import json
import time
import random
import os

HOST = '127.0.0.1'
PORT = 6004

def generate_random_staff(count=25):
    """임의의 직원 정보 생성"""
    first_names = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권", "황", "안", "송", "류", "전"]
    last_names = ["민수", "영희", "철수", "영수", "정희", "현우", "지영", "승호", "미영", "태현", "소영", "준호", "혜진", "상훈", "은정", "도현", "채영", "진우", "수빈", "예준"]
    
    grade_distribution = {
        1: ("수간호사", 3),      
        2: ("주임간호사", 5),    
        3: ("일반간호사", 9),   
        4: ("간호사", 4),      
        5: ("신규간호사", 4)     
    }
    
    staff = []
    staff_id = 1000
    
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

def test_recommended_scenario(test_id, shifts, shift_hours, staff_data, description, off_shifts=None):
    """권장 테스트 조건으로 테스트 수행"""
    custom_rules = {
        "shifts": shifts,
        "shift_hours": shift_hours
    }
    


    request = {
        "position": "간호",
        "shift_type": 3,
        "target_month": "2025-09",
        "staff_data": {
            "staff": staff_data
        },
        "custom_rules": custom_rules
    }
    
    print(f"\n{'='*60}")
    print(f"테스트 {test_id:2d}: {description}")
    print(f"{'='*60}")
    print(f"시프트: {shifts}")
    print(f"시간배정: {shift_hours}")
    print(f"직원 수: {len(staff_data)}명")
    
    # 수학적 검증
    non_off_shifts = [s for s in shifts if s not in  ['o', 'off', 'rest', '휴무', '쉼', 'free','Off','REST','Free']]
    max_daily_hours = sum(shift_hours[s] for s in non_off_shifts)
    max_monthly_hours = max_daily_hours * 31 # 보통 한달 31일 
    avg_target_hours = sum(staff["total_monthly_work_hours"] for staff in staff_data) / len(staff_data)
    
    print(f"수학적 검증:")
    print(f"  - 하루 최대 근무시간: {max_daily_hours}시간")
    print(f"  - 월 최대 가능시간: {max_monthly_hours}시간")
    print(f"  - 직원 평균 목표시간: {avg_target_hours:.1f}시간")
    
    response, generation_time = send_request(request)
    
    if response:
        if response.get("status") == "ok":
            print(f"✅ 성공 - {generation_time:.2f}초")
            
            # 결과 저장
            os.makedirs("./client_data", exist_ok=True)
            output_file = f"./client_data/recommended_test_{test_id:02d}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(response["schedule"], f, ensure_ascii=False, indent=2)
            print(f"📁 저장: {output_file}")
            
            # 신규간호사 야간 근무 확인
            if 'N' in shifts or any('night' in s.lower() or '야간' in s or '밤' in s for s in shifts):
                schedule = response["schedule"]
                newbie_night_count = 0
                night_shifts = [s for s in shifts if 'N' == s or 'night' in s.lower() or '야간' in s or '밤' in s]
                
                for date, day_schedule in schedule.items():
                    for shift_info in day_schedule:
                        if shift_info["shift"] in night_shifts:
                            for person in shift_info["people"]:
                                if person["grade"] == 5:  # 신규간호사
                                    newbie_night_count += 1
                
                print(f"📊 신규간호사 야간 근무: {newbie_night_count}회")
                print(f"📊 신규간호사 보호: {'✅ 적용됨' if newbie_night_count == 0 else '❌ 미적용'}")
            
            return True, generation_time
        else:
            print(f"❌ 실패 - {response}")
            return False, generation_time
    else:
        print(f"🚨 오류 - 응답 없음")
        return False, 0

def run_recommended_tests():
    """권장 테스트 조건으로 15개 시나리오 실행"""
    
    print("=== 권장 테스트 조건 기반 15개 시나리오 ===")
    print("✅ 각 시프트 6시간 이상")
    print("✅ 2-4교대 시스템")
    print("✅ 하루 총 근무시간 18-24시간")
    print("✅ 수학적 검증 완료")
    
    # 공통 직원 데이터 생성
    common_staff = generate_random_staff(23)
    
    # 권장 테스트 시나리오들
    # test_scenarios = [
    #     # 2교대 시스템 (5개)
    #     {
    #         "shifts": ["주간", "야간", "휴무"],
    #         "shift_hours": {"주간": 12, "야간": 12, "휴무": 0},
    #         "description": "2교대 한글 12시간 시스템"
    #     },
    #     {
    #         "shifts": ["Day", "Night", "Off"],
    #         "shift_hours": {"Day": 10, "Night": 14, "Off": 0},
    #         "description": "2교대 영문 비대칭 시간"
    #     },
    #     {
    #         "shifts": ["오전", "오후", "쉼"],
    #         "shift_hours": {"오전": 8, "오후": 16, "쉼": 0},
    #         "description": "2교대 오전-오후 시스템"
    #     },
    #     {
    #         "shifts": ["Early", "Late", "REST"],
    #         "shift_hours": {"Early": 9, "Late": 15, "REST": 0},
    #         "description": "2교대 Early-Late 시스템"
    #     },
    #     {
    #         "shifts": ["A", "B", "O"],
    #         "shift_hours": {"A": 11, "B": 13, "O": 0},
    #         "description": "2교대 A-B 시스템"
    #     },
        
    #     # 3교대 시스템 (5개)
    #     # {
    #     #     "shifts": ["D", "E", "N", "O"],
    #     #     "shift_hours": {"D": 8, "E": 8, "N": 8, "O": 0},
    #     #     "description": "3교대 표준 시스템"
    #     # },
    #     {
    #         "shifts": ["아침", "저녁", "밤", "휴무"],
    #         "shift_hours": {"아침": 8, "저녁": 8, "밤": 8, "휴무": 0},
    #         "description": "3교대 한글 시스템"
    #     },
    #     {
    #         "shifts": ["Morning", "Evening", "Night", "Off"],
    #         "shift_hours": {"Morning": 7, "Evening": 8, "Night": 9, "Off": 0},
    #         "description": "3교대 영문 비대칭"
    #     },
    #     {
    #         "shifts": ["06-14", "14-22", "22-06", "Off"],
    #         "shift_hours": {"06-14": 8, "14-22": 8, "22-06": 8, "Off": 0},
    #         "description": "3교대 시간대 표기"
    #     },
    #     {
    #         "shifts": ["Shift1", "Shift2", "Shift3", "Free"],
    #         "shift_hours": {"Shift1": 8, "Shift2": 8, "Shift3": 8, "Free": 0},
    #         "description": "3교대 번호 시스템"
    #     },
        
    #     # 4교대 시스템 (3개) - 시간 증가로 수정
    #     {
    #         "shifts": ["새벽", "오전", "오후", "밤", "휴무"],
    #         "shift_hours": {"새벽": 8, "오전": 8, "오후": 8, "밤": 8, "휴무": 0},
    #         "description": "4교대 한글 8시간"
    #     },       
    #     {
    #         "shifts": ["Alpha", "Beta", "Gamma", "Delta", "REST"],
    #         "shift_hours": {"Alpha": 8, "Beta": 7, "Gamma": 7, "Delta": 8, "REST": 0},
    #         "description": "4교대 그리스 문자 혼합시간"
    #     },
        
    #     # 특수 시스템 (2개)
    #     {
    #         "shifts": ["LongDay", "ShortNight", "Off"],
    #         "shift_hours": {"LongDay": 16, "ShortNight": 8, "Off": 0},
    #         "description": "특수 Long-Short 시스템"
    #     },
    #     {
    #         "shifts": ["FullShift", "HalfShift", "Off"],
    #         "shift_hours": {"FullShift": 12, "HalfShift": 6, "Off": 0},
    #         "description": "특수 Full-Half 시스템"
    #     }
    # ]
    
    # 좀더 현실적 시나리오
    test_scenarios = [
    {
        "shifts": ["Day", "Night", "Off"],
        "shift_hours": {"Day": 12, "Night": 12, "Off": 0},
        "description": "2교대 표준 시스템"
    },
    {
        "shifts": ["D", "N", "O"],
        "shift_hours": {"D": 10, "N": 14, "O": 0},
        "description": "2교대 비대칭 시스템"
    },
    {
        "shifts": ["주간", "야간", "휴무"],
        "shift_hours": {"주간": 12, "야간": 12, "휴무": 0},
        "description": "2교대 한글 시스템"
    },
    {
        "shifts": ["AM", "PM", "Night", "Off"],
        "shift_hours": {"AM": 6, "PM": 6, "Night": 12, "Off": 0},
        "description": "요양병원 2.5교대"
    },
    {
        "shifts": ["오전", "야간", "휴무"],
        "shift_hours": {"오전": 8, "야간": 16, "휴무": 0},
        "description": "야간 16시간형"
    },
    {
        "shifts": ["D", "E", "N", "Off"],
        "shift_hours": {"D": 8, "E": 8, "N": 8, "Off": 0},
        "description": "3교대 병원 표준"
    },
    {
        "shifts": ["Morning", "Evening", "Night", "Off"],
        "shift_hours": {"Morning": 8, "Evening": 8, "Night": 8, "Off": 0},
        "description": "3교대 영문 시스템"
    },
    {
        "shifts": ["06-14", "14-22", "22-06", "Off"],
        "shift_hours": {"06-14": 8, "14-22": 8, "22-06": 8, "Off": 0},
        "description": "3교대 시간대 표기"
    },
    {
        "shifts": ["D", "E", "N", "O"],
        "shift_hours": {"D": 8, "E": 8, "N": 6, "O": 0},
        "description": "3교대 야간단축형"
    },
    {
        "shifts": ["FullDay", "HalfDay", "Night", "Off"],
        "shift_hours": {"FullDay": 8, "HalfDay": 4, "Night": 8, "Off": 0},
        "description": "파트타임 포함형"
    },
    {
        "shifts": ["Day", "Evening", "Night", "Off"],
        "shift_hours": {"Day": 9, "Evening": 7, "Night": 8, "Off": 0},
        "description": "병원형 유연 3교대"
    },
    {
        "shifts": ["M", "A", "N", "R"],
        "shift_hours": {"M": 8, "A": 8, "N": 8, "R": 0},
        "description": "3교대 축약형"
    },
    {
        "shifts": ["오전", "오후", "심야", "휴무"],
        "shift_hours": {"오전": 7, "오후": 7, "심야": 10, "휴무": 0},
        "description": "장시간 심야형"
    },
    {
        "shifts": ["Day", "Night", "Off"],
        "shift_hours": {"Day": 11, "Night": 13, "Off": 0},
        "description": "2교대 비율조정형"
    }
]

    
    # 결과 추적
    success_count = 0
    total_time = 0
    results = []
    
    # 각 시나리오 실행
    for i, scenario in enumerate(test_scenarios, 1):
        # 각 테스트마다 다른 직원 데이터 생성 (변화 추가)
        staff_data = generate_random_staff(25)
        
        success, gen_time = test_recommended_scenario(
            i,
            scenario["shifts"],
            scenario["shift_hours"],
            staff_data,
            scenario["description"]
        )
        
        if success:
            success_count += 1
        
        total_time += gen_time
        results.append({
            "test_id": i,
            "description": scenario["description"],
            "success": success,
            "time": gen_time,
            "shifts": len(scenario["shifts"]) - 1,  # 휴무 제외
            "max_daily_hours": sum(h for s, h in scenario["shift_hours"].items() if h > 0)
        })
        
        time.sleep(0.1)  # 서버 부담 줄이기
    
    # 최종 결과 출력
    print(f"\n{'='*60}")
    print(f"🏆 최종 테스트 결과")
    print(f"{'='*60}")
    print(f"총 테스트: {len(test_scenarios)}개")
    print(f"성공: {success_count}개 ({success_count/len(test_scenarios)*100:.1f}%)")
    print(f"실패: {len(test_scenarios)-success_count}개")
    print(f"평균 생성 시간: {total_time/len(test_scenarios):.2f}초")
    print(f"총 소요 시간: {total_time:.2f}초")
    
    # 상세 결과 출력
    print(f"\n📊 테스트별 상세 결과:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test_id']:2d}. {result['description']:<25} - {result['time']:5.2f}초 ({result['shifts']}교대, {result['max_daily_hours']}h/day)")
    
    # 실패한 테스트가 있다면 분석
    failed_tests = [r for r in results if not r["success"]]
    if failed_tests:
        print(f"\n🚨 실패 테스트 분석:")
        for test in failed_tests:
            print(f"   테스트 {test['test_id']}: {test['description']}")
            print(f"   - {test['shifts']}교대, 하루 최대 {test['max_daily_hours']}시간")
    
    # 성능 분석
    if success_count > 0:
        successful_tests = [r for r in results if r["success"]]
        avg_success_time = sum(r["time"] for r in successful_tests) / len(successful_tests)
        fastest = min(successful_tests, key=lambda x: x["time"])
        slowest = max(successful_tests, key=lambda x: x["time"])
        
        print(f"\n⚡ 성능 분석:")
        print(f"성공 테스트 평균 시간: {avg_success_time:.2f}초")
        print(f"최고 성능: {fastest['time']:.2f}초 (테스트 {fastest['test_id']})")
        print(f"최저 성능: {slowest['time']:.2f}초 (테스트 {slowest['test_id']})")
    
    print(f"\n📁 생성된 파일들: ./client_data/recommended_test_*.json")
    
    return success_count, len(test_scenarios), total_time

if __name__ == "__main__":
    print("권장 테스트 조건 기반 테스트 클라이언트")
    print("서버가 실행 중인지 확인하세요 (포트 6002)")
    
    success, total, time_taken = run_recommended_tests()
    
    if success == total:
        print(f"\n🎉 모든 테스트 성공! ({success}/{total})")
    else:
        print(f"\n⚠️  일부 테스트 실패 ({success}/{total})")
    
    print(f"테스트 완료 - 총 {time_taken:.1f}초 소요")