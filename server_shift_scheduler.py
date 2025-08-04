from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import os
import json
import socket

PORT = 6000

def create_individual_shift_schedule(request_json):
    # JSON에서 필요한 데이터 추출
    staff_data = request_json.get("staff_data", {})
    all_people = staff_data.get("staff", [])
    shift_type = request_json.get("shift_type", 3)
    change_requests = request_json.get("change_requests", [])

    if shift_type not in [2, 3, 4]:
        raise ValueError("shift_type must be 2, 3, or 4")

    model = cp_model.CpModel()

    # Define shifts based on shift_type
    if shift_type == 2:
        shifts = ['D', 'N', 'O']  # Day, Night, Off
        night_shift = 'N'
    elif shift_type == 3:
        shifts = ['D', 'E', 'N', 'O']  # Day, Evening, Night, Off
        night_shift = 'N'
    elif shift_type == 4:
        shifts = ['M', 'D', 'E', 'N', 'O']  # Morning, Day, Evening, Night, Off
        night_shift = 'N'

    shift_hours = {s: 8 if s != 'O' else 0 for s in shifts}
    num_days = 31
    days = range(num_days)
    start_date = datetime(2025, 8, 1)
    num_weeks = (num_days + 6) // 7

    # Check maximum 5 unique grades
    unique_grades = set(person["grade"] for person in all_people)
    if len(unique_grades) > 5:
        raise ValueError("Up to 5 unique grades are supported.")

    # 변수 생성 (staff_id, day, shift)
    schedule = {}
    for person in all_people:
        sid = str(person["staff_id"])
        for d in days:
            for s in shifts:
                schedule[(sid, d, s)] = model.NewBoolVar(f"{sid}_d{d}_{s}")

    # 변경 요청 주석처리 (필요시 해제)
    # for req in change_requests:
    #     sid = str(req["staff_id"])
    #     req_date = datetime.strptime(req["date"], '%Y-%m-%d')
    #     d = (req_date - start_date).days
    #     s = req["desired_shift"]
    #     if 0 <= d < num_days and s in shifts and sid in [str(p["staff_id"]) for p in all_people]:
    #         model.Add(schedule[(sid, d, s)] == 1)

    # 직원별 한 날에 정확히 한 개 shift 배정 : 유지!
    for person in all_people:
        sid = str(person["staff_id"])
        for d in days:
            model.AddExactlyOne([schedule[(sid, d, s)] for s in shifts])

    # 각 날짜별 Off 제외한 모든 시프트에 최소 1명 배정 -> 변경 
    # for d in days:
    #     for s in shifts:
    #         if s != 'O':
    #             model.Add(sum(schedule[(str(person["staff_id"]), d, s)] for person in all_people) >= 1)


    # Night shift 다음 날 Off, N 다음날 E 불가 : 강력 유지!
    for person in all_people:
        sid = str(person["staff_id"])
        for d in range(num_days - 1):
            night = schedule[(sid, d, night_shift)]
            off_next = schedule[(sid, d + 1, 'O')]
            model.AddImplication(night, off_next)
            if 'E' in shifts:
                eve_next = schedule[(sid, d + 1, 'E')]
                model.AddBoolOr([night.Not(), eve_next.Not()])

    # 최소 3일 Off : 유지
    for person in all_people:
        sid = str(person["staff_id"])
        model.Add(sum(schedule[(sid, d, 'O')] for d in days) >= 3)

    # 주 단위 최대 40시간 (기존 제약) : 40->48 로 현실반영 
    for person in all_people:
        sid = str(person["staff_id"])
        for w in range(num_weeks):
            week_start = w * 7
            week_end = min(week_start + 7, num_days)
            hours = sum(schedule[(sid, d, s)] * shift_hours[s] for d in range(week_start, week_end) for s in shifts)
            model.Add(hours <= 48)

    # ** 월 최대 근무시간 제약 추가 **
    monthly_hours_limit = {str(p["staff_id"]): p.get("total_monthly_work_hours", 160) for p in all_people}
    for person in all_people:
        sid = str(person["staff_id"])
        model.Add(
            sum(schedule[(sid, d, s)] * shift_hours[s] for d in days for s in shifts)
            <= monthly_hours_limit[sid]
        )

    # Night shift 균형 맞추기
    night_counts = [sum(schedule[(str(person["staff_id"]), d, night_shift)] for d in days) for person in all_people]
    max_nights = model.NewIntVar(0, num_days, "max_night")
    min_nights = model.NewIntVar(0, num_days, "min_night")
    model.AddMaxEquality(max_nights, night_counts)
    model.AddMinEquality(min_nights, night_counts)
    model.Minimize(max_nights - min_nights)

    # 솔버 설정 및 실행
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0
    solver.parameters.log_search_progress = True
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    print(f"솔버 상태: {solver.StatusName(status)}")
    if status == cp_model.INFEASIBLE:
        model.ExportToFile("model_dump.txt")
        print("모델 덤프됨: model_dump.txt → OR-Tools CP-SAT Visualizer로 확인 가능")
        return None
    elif status == cp_model.MODEL_INVALID:
        print("[ERROR] 모델 유효하지 않음")
        return None
    elif status == cp_model.UNKNOWN:
        print("[WARNING] 솔버 해 찾지 못함")
        return None

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


# TCP 소켓 서버 예시 (간단히 구현)
def run_server(host='127.0.0.1', port=PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"서버 실행 중... {host}:{port}")
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"클라이언트 연결: {addr}")
                data = b""
                while True:
                    part = conn.recv(4096)
                    if not part:
                        break
                    data += part
                try:
                    request_json = json.loads(data.decode())
                    print(f"요청 데이터 수신: {request_json}")
                    result = create_individual_shift_schedule(request_json)
                    response = {"status": "ok"}
                    if result:
                        response.update(result)
                    else:
                        response["status"] = "error"
                        response["message"] = "스케줄 생성 실패"
                except Exception as e:
                    response = {"status": "error", "message": str(e)}

                response_str = json.dumps(response, ensure_ascii=False)
                conn.sendall(response_str.encode())
                print(f"응답 전송 완료")

if __name__ == "__main__":
    run_server()


