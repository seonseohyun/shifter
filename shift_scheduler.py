from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import os
import json

def create_individual_shift_schedule(staff_data, shift_type):
    if shift_type not in [2, 3, 4]:
        raise ValueError("shift_type must be 2, 3, or 4")

    model = cp_model.CpModel()

    # Define shifts based on shift_type
    if shift_type == 2:
        shifts = ['D', 'N', 'O']  # Day, Night, Off
        night_shift = 'N'  # The night shift label
    elif shift_type == 3:
        shifts = ['D', 'E', 'N', 'O']  # Day, Evening, Night, Off
        night_shift = 'N'
    elif shift_type == 4:
        shifts = ['M', 'D', 'E', 'N', 'O']  # Morning, Day, Evening, Night, Off (inspired by image)
        night_shift = 'N'

    shift_hours = {s: 8 if s != 'O' else 0 for s in shifts}
    num_days = 31
    days = range(num_days)
    start_date = datetime(2025, 8, 1)
    num_weeks = (num_days + 6) // 7

    # Extract all individuals
    all_people = staff_data["staff"]

    # Check for maximum 5 unique grades
    unique_grades = set(person["grade"] for person in all_people)
    if len(unique_grades) > 5:
        raise ValueError("Up to 5 unique grades are supported.")

    # Variables: (staff_id, day, shift)
    schedule = {}
    for person in all_people:
        sid = str(person["staff_id"])  # Ensure staff_id is string
        for d in days:
            for s in shifts:
                schedule[(sid, d, s)] = model.NewBoolVar(f"{sid}_d{d}_{s}")

    
    # Load and apply change requests from JSON
    change_requests_path = "./data/change_requests.json"
    change_requests = []
    if os.path.exists(change_requests_path):
        try:
            with open(change_requests_path, "r", encoding="utf-8") as f:
                change_requests = json.load(f)
        except Exception as e:
            print(f"[WARNING] JSON 파일 읽기 오류: {e}")

    change_applied = False
    for req in change_requests:
        try:
            sid = str(req["staff_id"])
            req_date = datetime.strptime(req["date"], '%Y-%m-%d')
            d = (req_date - start_date).days
            s = req["desired_shift"]
            original_s = req.get("original_shift", "알수없음")
            
            if 0 <= d < num_days and s in shifts and sid in [str(p["staff_id"]) for p in all_people]:
                model.Add(schedule[(sid, d, s)] == 1)
                change_applied = True
                print(f"[INFO] {sid}의 {req['date']} 근무를 {original_s}에서 {s}로 변경 요청 적용")
            else:
                print(f"[WARNING] 유효하지 않은 요청: staff_id={sid}, date={req['date']}, shift={s}")
        except Exception as e:
            print(f"[WARNING] 요청 처리 오류: {e}")

    if not change_applied and change_requests:
        print("[WARNING] 변경 요청이 있었지만 적용된 것이 없습니다.")
    elif change_applied:
        print(f"[INFO] 총 {len([req for req in change_requests if str(req['staff_id']) in [str(p['staff_id']) for p in all_people]])}개의 변경 요청이 적용되었습니다.")


    # Each individual has exactly one shift per day
    for person in all_people:
        sid = str(person["staff_id"])
        for d in days:
            model.AddExactlyOne([schedule[(sid, d, s)] for s in shifts])

    # Each day, at least one person per required shift (all except O)
    for d in days:
        for s in shifts:
            if s != 'O':
                model.Add(sum(schedule[(str(person["staff_id"]), d, s)] for person in all_people) >= 1)

    # Night shift followed by Off, and no E after N (adapt for shift_type)
    for person in all_people:
        sid = str(person["staff_id"])
        for d in range(num_days - 1):
            night = schedule[(sid, d, night_shift)]
            off_next = schedule[(sid, d + 1, 'O')]
            model.AddImplication(night, off_next)

            # For shift_type >=3, prevent E after N (if E exists)
            if 'E' in shifts:
                eve_next = schedule[(sid, d + 1, 'E')]
                model.AddBoolOr([night.Not(), eve_next.Not()])

    # Minimum 3 Off days per individual over the period
    for person in all_people:
        sid = str(person["staff_id"])
        model.Add(sum(schedule[(sid, d, 'O')] for d in days) >= 3)

    # Weekly hours <= 40 per individual
    for person in all_people:
        sid = str(person["staff_id"])
        for w in range(num_weeks):
            week_start = w * 7
            week_end = min(week_start + 7, num_days)
            hours = sum(schedule[(sid, d, s)] * shift_hours[s] for d in range(week_start, week_end) for s in shifts)
            model.Add(hours <= 40)

    # Balance Night shifts across individuals
    night_counts = [sum(schedule[(str(person["staff_id"]), d, night_shift)] for d in days) for person in all_people]
    max_nights = model.NewIntVar(0, num_days, "max_night")
    min_nights = model.NewIntVar(0, num_days, "min_night")
    model.AddMaxEquality(max_nights, night_counts)
    model.AddMinEquality(min_nights, night_counts)
    model.Minimize(max_nights - min_nights)

    # Solve the model
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300.0
    solver.parameters.log_search_progress = True
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    print(f"솔버 상태: {solver.StatusName(status)}")
    if status == cp_model.INFEASIBLE:
        print("[ERROR] 제약 조건 모순 발생 - 변경 요청을 만족하는 근무표를 생성할 수 없습니다.")
        if change_applied:
            print("[ERROR] 변경 요청이 적용되었지만 해가 없습니다. 요청한 변경사항이 다른 제약조건과 충돌합니다.")
        return None
    elif status == cp_model.MODEL_INVALID:
        print("[ERROR] 모델이 유효하지 않습니다.")
        return None
    elif status == cp_model.UNKNOWN:
        print("[WARNING] 솔버가 해를 찾지 못했습니다 (시간 초과 또는 기타 이유)")
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

        output_path = "./data/time_table.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"[INFO] 시간표가 저장되었습니다: {output_path}")
        if change_applied:
            print("[SUCCESS] 변경 요청이 성공적으로 반영되어 새로운 근무표가 생성되었습니다.")
        else:
            print("[INFO] 변경 요청 없이 기본 근무표가 생성되었습니다.")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result
    else:
        print("[ERROR] 해를 찾을 수 없습니다.")
        return None



#staff_data가 팀개념으로 근무표가 생성될것이고
#staff_data를 앞으로는 client가 json안에 요청을해서 python에서 참조하여 근무표를 생성하도록 변경
staff_data  = {
    "staff": [
        {"name": "박주영", "staff_id": 101, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "최정환", "staff_id": 102, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "문재윤", "staff_id": 103, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "선서현", "staff_id": 104, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "박경태", "staff_id": 105, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "유희라", "staff_id": 106, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "김유범", "staff_id": 107, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "박서은", "staff_id": 108, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "김대업", "staff_id": 109, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "유예솜", "staff_id": 110, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "고준영", "staff_id": 111, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "하진영", "staff_id": 112, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "오장관", "staff_id": 113, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "윤진영", "staff_id": 114, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "한경식", "staff_id": 115, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "한현희", "staff_id": 116, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "정종옥", "staff_id": 117, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "양성규", "staff_id": 118, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "김화백", "staff_id": 119, "grade": 1, "grade_name": "제일높은직급"},
        {"name": "이병희", "staff_id": 120, "grade": 1, "grade_name": "제일높은직급"}
    ]
}

if __name__ == "__main__":
    # Example usage: choose shift_type as 2, 3, or 4
    shift_type = 3  # Change this to 2 or 4 as needed
    create_individual_shift_schedule(staff_data, shift_type)