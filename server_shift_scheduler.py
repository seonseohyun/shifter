import socket
import json
from datetime import datetime, timedelta
from ortools.sat.python import cp_model
import os

HOST = '127.0.0.1'
PORT = 6000

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

    # # Apply change requests (currently disabled)
    # change_applied = False
    # if change_requests:
    #     for req in change_requests:
    #         try:
    #             sid = str(req["staff_id"])
    #             req_date = datetime.strptime(req["date"], '%Y-%m-%d')
    #             d = (req_date - start_date).days
    #             s = req["desired_shift"]
    #             original_s = req.get("original_shift", "알수없음")
    #
    #             if 0 <= d < num_days and s in shifts and sid in [str(p["staff_id"]) for p in all_people]:
    #                 model.Add(schedule[(sid, d, s)] == 1)
    #                 change_applied = True
    #                 print(f"[INFO] {sid}의 {req['date']} 근무를 {original_s}에서 {s}로 변경 요청 적용")
    #             else:
    #                 print(f"[WARNING] 유효하지 않은 요청: staff_id={sid}, date={req['date']}, shift={s}")
    #         except Exception as e:
    #             print(f"[WARNING] 요청 처리 오류: {e}")

    for person in all_people:
        sid = str(person["staff_id"])
        for d in days:
            model.AddExactlyOne([schedule[(sid, d, s)] for s in shifts])

    for d in days:
        for s in shifts:
            if s != 'O':
                model.Add(sum(schedule[(str(person["staff_id"]), d, s)] for person in all_people) >= 1)

    for person in all_people:
        sid = str(person["staff_id"])
        for d in range(num_days - 1):
            night = schedule[(sid, d, night_shift)]
            off_next = schedule[(sid, d + 1, 'O')]
            model.AddImplication(night, off_next)

            if 'E' in shifts:
                eve_next = schedule[(sid, d + 1, 'E')]
                model.AddBoolOr([night.Not(), eve_next.Not()])

    for person in all_people:
        sid = str(person["staff_id"])
        model.Add(sum(schedule[(sid, d, 'O')] for d in days) >= 3)

    for person in all_people:
        sid = str(person["staff_id"])
        for w in range(num_weeks):
            week_start = w * 7
            week_end = min(week_start + 7, num_days)
            hours = sum(schedule[(sid, d, s)] * shift_hours[s] for d in range(week_start, week_end) for s in shifts)
            model.Add(hours <= 40)

    night_counts = [sum(schedule[(str(person["staff_id"]), d, night_shift)] for d in days) for person in all_people]
    max_nights = model.NewIntVar(0, num_days, "max_night")
    min_nights = model.NewIntVar(0, num_days, "min_night")
    model.AddMaxEquality(max_nights, night_counts)
    model.AddMinEquality(min_nights, night_counts)
    model.Minimize(max_nights - min_nights)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300.0
    solver.parameters.log_search_progress = True
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    print(f"솔버 상태: {solver.StatusName(status)}")
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        result = {}
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
