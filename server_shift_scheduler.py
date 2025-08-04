import socket
import json
from datetime import datetime, timedelta
from ortools.sat.python import cp_model
import os

HOST = '127.0.0.1'
PORT = 6001

# 직군별 제약조건 정의
POSITION_RULES = {
    "간호": {
        "min_off_days": 3,
        "newbie_no_night": True,
        "night_after_off": True,
        "max_weekly_hours": 60,
        "max_monthly_hours": 180,
        "newbie_grade": 5,  # 신규간호사 등급
        "shifts": ['D', 'E', 'N', 'O'],  # 3교대
        "shift_hours": {'D': 8, 'E': 8, 'N': 8, 'O': 0}
    },
    "소방": {
        "shift_cycle": "D24-O-O",
        "duty_per_cycle": 1,
        "night_after_off": True,
        "max_weekly_hours": 72,
        "max_monthly_hours": 192,
        "cycle_days": 3,  # 3일 주기
        "shifts": ['D24', 'O'],  # 24시간 당직, 오프
        "shift_hours": {'D24': 24, 'O': 0}
    },
    "default": {  # 기본 제약조건 (기존 로직)
        "min_off_days": 2,
        "night_after_off": True,
        "max_weekly_hours": 60,
        "max_monthly_hours": 180,
        "shifts": ['D', 'E', 'N', 'O'],
        "shift_hours": {'D': 8, 'E': 8, 'N': 8, 'O': 0}
    }
}

def apply_position_constraints(model, schedule, person, days, shifts, shift_hours, num_weeks, rules, position):
    """직군별 제약조건 적용"""
    sid = str(person["staff_id"])
    grade = person.get("grade", 1)
    name = person.get("name", f"staff_{sid}")
    
    print(f"[INFO] {name} ({position}) 제약조건 적용 중...")
    
    if position == "간호":
        # 신규간호사는 야간 근무 금지
        if rules.get("newbie_no_night", False) and grade == rules.get("newbie_grade", 5):
            if 'N' in shifts:
                for d in days:
                    model.Add(schedule[(sid, d, 'N')] == 0)
                print(f"[INFO] {name}: 신규간호사 야간 근무 금지 적용")
        
        # 야간 근무 후 반드시 휴무
        if rules.get("night_after_off", False) and 'N' in shifts and 'O' in shifts:
            for d in range(len(days) - 1):
                night = schedule[(sid, d, 'N')]
                off_next = schedule[(sid, d + 1, 'O')]
                model.AddImplication(night, off_next)
                
                # 야간 근무 후 다른 근무 금지
                if 'D' in shifts:
                    day_next = schedule[(sid, d + 1, 'D')]
                    model.AddBoolOr([night.Not(), day_next.Not()])
                if 'E' in shifts:
                    eve_next = schedule[(sid, d + 1, 'E')]
                    model.AddBoolOr([night.Not(), eve_next.Not()])
        
        # 최소 휴무일
        min_off_days = rules.get("min_off_days", 3)
        if 'O' in shifts:
            model.Add(sum(schedule[(sid, d, 'O')] for d in days) >= min_off_days)
            print(f"[INFO] {name}: 최소 휴무일 {min_off_days}일 적용")
    
    elif position == "소방":
        # 소방 직군 제약조건 (완화된 버전)
        if 'D24' in shifts and 'O' in shifts:
            # D24 후 반드시 오프 (최소 1일)
            for d in range(len(days) - 1):
                d24_today = schedule[(sid, d, 'D24')]
                off_tomorrow = schedule[(sid, d + 1, 'O')]
                model.AddImplication(d24_today, off_tomorrow)
            
            # 월 D24 근무 횟수 제한 (월 8-12회 정도)
            monthly_d24 = sum(schedule[(sid, d, 'D24')] for d in days)
            model.Add(monthly_d24 >= 8)  # 최소 8회
            model.Add(monthly_d24 <= 12) # 최대 12회
            
            print(f"[INFO] {name}: 소방 D24 후 오프 제약 적용 (월 8-12회)")
    
    # 공통 제약조건
    # 주당 근무시간 제한
    max_weekly_hours = rules.get("max_weekly_hours", 60)
    for w in range(num_weeks):
        week_start = w * 7
        week_end = min(week_start + 7, len(days))
        weekly_hours = sum(schedule[(sid, d, s)] * shift_hours[s] 
                          for d in range(week_start, week_end) for s in shifts)
        model.Add(weekly_hours <= max_weekly_hours)
    
    # 월 총 근무시간 제한
    base_monthly_hours = person.get("total_monthly_work_hours", rules.get("max_monthly_hours", 180))
    max_monthly_hours = int(base_monthly_hours * 1.1)  # 10% 여유분
    monthly_hours = sum(schedule[(sid, d, s)] * shift_hours[s] for d in days for s in shifts)
    model.Add(monthly_hours <= max_monthly_hours)
    
    print(f"[INFO] {name}: 주당 최대 {max_weekly_hours}시간, 월 최대 {base_monthly_hours}시간(여유분: {max_monthly_hours}시간)")

def create_individual_shift_schedule(staff_data, shift_type, change_requests=None, position="default"):
    model = cp_model.CpModel()
    
    # 직군별 규칙 가져오기
    rules = POSITION_RULES.get(position, POSITION_RULES["default"])
    print(f"[INFO] 직군: {position}, 적용 규칙: {list(rules.keys())}")
    
    # 직군별 시프트 정의 사용
    if position in POSITION_RULES:
        shifts = rules["shifts"]
        shift_hours = rules["shift_hours"]
        night_shift = 'N' if 'N' in shifts else None
    else:
        # 기존 로직 유지 (호환성)
        if shift_type not in [2, 3, 4]:
            raise ValueError("shift_type must be 2, 3, or 4")
            
        if shift_type == 2:
            shifts = ['D', 'N', 'O']
            night_shift = 'N'
        elif shift_type == 3:
            shifts = ['D', 'E', 'N', 'O']
            night_shift = 'N'
        elif shift_type == 4:
            shifts = ['M', 'D', 'E', 'N', 'O']
            night_shift = 'N'
        
        shift_hours = {s: 8 if s != 'O' else 0 for s in shifts}
    num_days = 31
    days = range(num_days)
    start_date = datetime(2025, 8, 1)
    num_weeks = (num_days + 6) // 7

    all_people = staff_data["staff"]

    unique_grades = set(person["grade"] for person in all_people)
    if len(unique_grades) > 5:
        raise ValueError("Up to 5 unique grades are supported.")

    schedule = {}
    for person in all_people:
        sid = str(person["staff_id"])
        for d in days:
            for s in shifts:
                schedule[(sid, d, s)] = model.NewBoolVar(f"{sid}_d{d}_{s}")    

    for person in all_people:
        sid = str(person["staff_id"])
        for d in days:
            model.AddExactlyOne([schedule[(sid, d, s)] for s in shifts])

    # 각 교대에 최소 인원 보장 (오프 제외)
    for d in days:
        for s in shifts:
            if s != 'O':
                model.Add(sum(schedule[(str(person["staff_id"]), d, s)] for person in all_people) >= 1)

    # 직군별 제약조건 적용
    for person in all_people:
        person_position = person.get("position", position)  # 개별 직원의 position 우선, 없으면 전체 position 사용
        person_rules = POSITION_RULES.get(person_position, rules)
        apply_position_constraints(model, schedule, person, days, shifts, shift_hours, num_weeks, person_rules, person_position)

    # 야간 근무 균등 분배 (야간 근무가 있는 경우만)
    if night_shift and night_shift in shifts:
        night_counts = [sum(schedule[(str(person["staff_id"]), d, night_shift)] for d in days) for person in all_people]
        max_nights = model.NewIntVar(0, num_days, "max_night")
        min_nights = model.NewIntVar(0, num_days, "min_night")
        model.AddMaxEquality(max_nights, night_counts)
        model.AddMinEquality(min_nights, night_counts)
        
        # 목적함수: 야간 근무 균등성
        model.Minimize(max_nights - min_nights)
        print(f"[INFO] 야간 근무 균등 분배 활성화 (야간 시프트: {night_shift})")
    else:
        print(f"[INFO] 야간 근무 균등 분배 비활성화 (직군: {position})")

    solver = cp_model.CpSolver()
    # 성능 우선 솔버 설정 (호환성 고려)
    solver.parameters.max_time_in_seconds = 30.0  # 시간을 30초로 대폭 단축
    solver.parameters.log_search_progress = False  # 로그 비활성화
    solver.parameters.num_search_workers = 1  # 단일 워커로 오버헤드 최소화
    solver.parameters.cp_model_presolve = True  # 전처리 활성화 유지
    status = solver.Solve(model)

    print(f"솔버 상태: {solver.StatusName(status)}")
    print(f"해결 시간: {solver.WallTime():.2f}초")
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        if night_shift and night_shift in shifts:
            night_balance_value = solver.Value(max_nights) - solver.Value(min_nights)
            print(f"야간 근무 균등성: {night_balance_value}")
            print(f"최대 야간 근무: {solver.Value(max_nights)}회, 최소 야간 근무: {solver.Value(min_nights)}회")
        else:
            print("야간 근무 없음 - 균등성 체크 생략")
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        result = {}
        monthly_hours_summary = {}
        
        # 근무표 생성
        for d in days:
            date_str = (start_date + timedelta(days=d)).strftime('%Y-%m-%d')
            day_schedule = []
            for s in shifts:
                assigned_people = []
                for person in all_people:
                    sid = str(person["staff_id"])
                    if solver.Value(schedule[(sid, d, s)]) == 1:
                        assigned_people.append({
                            "staff_id": sid,
                            "이름": person["name"],
                            "grade": person["grade"],
                            "grade_name": person["grade_name"]
                        })
                day_schedule.append({
                    "shift": s,
                    "people": assigned_people
                })
            result[date_str] = day_schedule
        
        # 월 총 근무시간 통계 계산
        for person in all_people:
            sid = str(person["staff_id"])
            total_hours = sum(solver.Value(schedule[(sid, d, s)]) * shift_hours[s] 
                            for d in days for s in shifts)
            monthly_hours_summary[person["name"]] = {
                "actual_hours": total_hours,
                "max_hours": person.get("total_monthly_work_hours", 180),
                "remaining_hours": person.get("total_monthly_work_hours", 180) - total_hours
            }
        
        print("\n=== 월 총 근무시간 통계 ===")
        for name, stats in monthly_hours_summary.items():
            print(f"{name}: {stats['actual_hours']}시간/{stats['max_hours']}시간 (여유: {stats['remaining_hours']}시간)")

          # JSON 파일로 저장
        output_path = "./data/result_schedule.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"[INFO] 근무표가 저장되었습니다: {output_path}")

        return result
    else:
        print("[ERROR] 해를 찾을 수 없습니다.")
        return None

def handle_request(request_json):
    try:
        data = json.loads(request_json)
        staff_data = data.get("staff_data")
        shift_type = data.get("shift_type", 3)
        change_requests = data.get("change_requests", [])
        position = data.get("position", "default")  # 직군 정보 추가

        if not staff_data or "staff" not in staff_data:
            return json.dumps({"error": "유효한 staff_data가 필요합니다."})

        print(f"[INFO] 요청 받음 - 직군: {position}, 직원 수: {len(staff_data['staff'])}")
        result = create_individual_shift_schedule(staff_data, shift_type, change_requests, position)

        if result is None:
            return json.dumps({"status": "error", "message": "근무표를 생성할 수 없습니다."})
        else:
            return json.dumps({"status": "ok", "schedule": result}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)})

def run_server():
    print(f"[INFO] 근무표 생성 Python 서버 시작됨: {HOST}:{PORT}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"[INFO] 연결됨: {addr}")
                data = conn.recv(65536).decode()
                if not data:
                    continue
                print(f"[DEBUG] 수신된 데이터: {data[:100]}...")
                response = handle_request(data)
                conn.sendall(response.encode('utf-8'))

if __name__ == "__main__":
    run_server()
