import socket
import json
from datetime import datetime, timedelta
from ortools.sat.python import cp_model
import os

HOST = '127.0.0.1'
PORT = 6001

def create_individual_shift_schedule(staff_data, shift_type, change_requests=None):
    if shift_type not in [2, 3, 4]:
        raise ValueError("shift_type must be 2, 3, or 4")

    model = cp_model.CpModel()

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

    for d in days:
        for s in shifts:
            if s != 'O':
                model.Add(sum(schedule[(str(person["staff_id"]), d, s)] for person in all_people) >= 1)

    # 야간 근무 후 휴무 규칙 - 하드 제약으로 단순화 (성능 향상)
    for person in all_people:
        sid = str(person["staff_id"])
        for d in range(num_days - 1):
            night = schedule[(sid, d, night_shift)]            
            off_next = schedule[(sid, d + 1, 'O')]
            
            # 하드 제약: 야간 근무 후 반드시 휴무
            model.AddImplication(night, off_next)

            # 야간 근무 후 저녁 근무 금지
            if 'E' in shifts:
                eve_next = schedule[(sid, d + 1, 'E')]
                model.AddBoolOr([night.Not(), eve_next.Not()])
            #야간 근무후 데이 근무 금지
            if 'D' in shifts:
                day_next = schedule[(sid, d+1, 'D')]
                model.AddBoolOr([night.Not(), day_next.Not()])

    # 최소 휴무일 제약 (월 최소 3일 → 2일로 완화) 
    for person in all_people:
        sid = str(person["staff_id"])
        model.Add(sum(schedule[(sid, d, 'O')] for d in days) >= 3)

    # 월 총 근무시간 제약조건 - 10% 여유분 추가 (현실성 고려)
    for person in all_people:  
        sid = str(person["staff_id"])
        base_hours = person.get("total_monthly_work_hours", 180)
        # 10% 여유분 추가하여 해 찾기 용이하게 함
        max_monthly_hours = int(base_hours * 1.1)
        monthly_hours = sum(schedule[(sid, d, s)] * shift_hours[s] for d in days for s in shifts)
        model.Add(monthly_hours <= max_monthly_hours)
        print(f"[INFO] {person['name']} 월 최대 근무시간: {base_hours}시간 (여유분 포함: {max_monthly_hours}시간)")

    # 주당 근무시간 제약을 대폭 완화 (40시간 → 50시간) 주당 근무시간은 유연하게 수정가능합니다.
    weely_hour_limit = 60
    for person in all_people:
        sid = str(person["staff_id"])
        for w in range(num_weeks):
            week_start = w * 7
            week_end = min(week_start + 7, num_days)
            hours = sum(schedule[(sid, d, s)] * shift_hours[s] for d in range(week_start, week_end) for s in shifts)
            model.Add(hours <= weely_hour_limit)  # 주당 최대 60시간으로 대폭 완화

    # 야간 근무 균등 분배 - 단순화된 목적함수
    night_counts = [sum(schedule[(str(person["staff_id"]), d, night_shift)] for d in days) for person in all_people]
    max_nights = model.NewIntVar(0, num_days, "max_night")
    min_nights = model.NewIntVar(0, num_days, "min_night")
    model.AddMaxEquality(max_nights, night_counts)
    model.AddMinEquality(min_nights, night_counts)


      #최소근무시간 제약
    margin = 25  # 예:209 -25 최소는 : 184시간  184/21 일 9.2시간근무

    for person in all_people:
        sid = str(person["staff_id"])
        max_hours = person.get("total_monthly_work_hours", 209)
        min_hours = max_hours - margin  # 최소 근무시간 설정

        monthly_work = sum(schedule[(sid, d, s)] * shift_hours[s] for d in days for s in shifts)

        model.Add(monthly_work <= max_hours)  # 최대 근무시간 제한
        model.Add(monthly_work >= min_hours)  # 최소 근무시간 제한
    
    # 단순한 목적함수: 야간 근무 균등성만
    model.Minimize(max_nights - min_nights)

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
        night_balance_value = solver.Value(max_nights) - solver.Value(min_nights)
        print(f"야간 근무 균등성: {night_balance_value}")
        print(f"최대 야간 근무: {solver.Value(max_nights)}회, 최소 야간 근무: {solver.Value(min_nights)}회")
    
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

        if not staff_data or "staff" not in staff_data:
            return json.dumps({"error": "유효한 staff_data가 필요합니다."})

        result = create_individual_shift_schedule(staff_data, shift_type, change_requests)

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
