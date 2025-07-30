from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import os
import json

def create_team_shift_schedule(team_json):
    model = cp_model.CpModel()

    # 설정
    shifts = ['D', 'E', 'N', 'O']  # Day, Evening, Night, Off
    shift_times = {
        'D': (datetime.strptime('09:00', '%H:%M').time(), datetime.strptime('17:00', '%H:%M').time()),
        'E': (datetime.strptime('14:00', '%H:%M').time(), datetime.strptime('22:00', '%H:%M').time()),
        'N': (datetime.strptime('22:00', '%H:%M').time(), datetime.strptime('06:00', '%H:%M').time()),
        'O': (None, None)
    }
    shift_hours = {'D': 8, 'E': 8, 'N': 8, 'O': 0}
    num_days = 30
    days = range(num_days)
    start_date = datetime(2025, 8, 1)
    num_weeks = (num_days + 6) // 7

    # 조 이름 및 인원 정리 (사번 추가)
    team_names = sorted(set(key.split()[0] for key in team_json if '팀장' in key))
    team_to_people = {}
    staff_id_counter = 101  # 사번 시작 번호
    for team in team_names:
        members = []
        # 팀장
        members.append({"staff_id": str(staff_id_counter), "name": team_json[f"{team} 팀장"]})
        staff_id_counter += 1
        # 팀원
        for member in team_json[f"{team} 팀원"]:
            members.append({"staff_id": str(staff_id_counter), "name": member})
            staff_id_counter += 1
        team_to_people[team] = members

    # 변수 생성
    schedule = {}
    for team in team_names:
        for d in days:
            schedule[(team, d)] = model.NewIntVar(0, len(shifts) - 1, f"{team}_day{d}")

    # 제약 1: 매일 D, E, N 중 하나 이상
    for d in days:
        for s in ['D', 'E', 'N']:
            shift_bools = []
            for team in team_names:
                is_shift = model.NewBoolVar(f"{team}_d{d}_{s}")
                model.Add(schedule[(team, d)] == shifts.index(s)).OnlyEnforceIf(is_shift)
                model.Add(schedule[(team, d)] != shifts.index(s)).OnlyEnforceIf(is_shift.Not())
                shift_bools.append(is_shift)
            model.Add(sum(shift_bools) >= 1)

    # 제약 2: Night 근무 다음 날 Off
    for team in team_names:
        for d in range(num_days - 1):
            night = model.NewBoolVar(f"{team}_d{d}_isN")
            model.Add(schedule[(team, d)] == shifts.index('N')).OnlyEnforceIf(night)
            model.Add(schedule[(team, d)] != shifts.index('N')).OnlyEnforceIf(night.Not())
            model.Add(schedule[(team, d + 1)] == shifts.index('O')).OnlyEnforceIf(night)
            # N 후 E 금지
            is_e = model.NewBoolVar(f"{team}_d{d+1}_E")
            model.Add(schedule[(team, d + 1)] == shifts.index('E')).OnlyEnforceIf(is_e)
            model.Add(schedule[(team, d + 1)] != shifts.index('E')).OnlyEnforceIf(is_e.Not())
            model.Add(night + is_e <= 1)

    # 새 제약: 전체 기간 최소 3일 Off (완화)
    for team in team_names:
        off_bools = []
        for d in days:
            is_off = model.NewBoolVar(f"{team}_d{d}_O")
            model.Add(schedule[(team, d)] == shifts.index('O')).OnlyEnforceIf(is_off)
            model.Add(schedule[(team, d)] != shifts.index('O')).OnlyEnforceIf(is_off.Not())
            off_bools.append(is_off)
        model.Add(sum(off_bools) >= 3)

    # 새 제약: 주 40시간 초과 금지
    for team in team_names:
        for w in range(num_weeks):
            week_start = w * 7
            week_end = min(week_start + 7, num_days)
            hours_var = model.NewIntVar(0, 100, f"{team}_w{w}_hours")
            hour_terms = []
            for d in range(week_start, week_end):
                for s in shifts:
                    is_s = model.NewBoolVar(f"{team}_d{d}_{s}")
                    model.Add(schedule[(team, d)] == shifts.index(s)).OnlyEnforceIf(is_s)
                    model.Add(schedule[(team, d)] != shifts.index(s)).OnlyEnforceIf(is_s.Not())
                    hour_terms.append(is_s * shift_hours[s])
            model.Add(sum(hour_terms) == hours_var)
            model.Add(hours_var <= 40)

    # 제약 3: Night 근무 균형
    night_counts = []
    for team in team_names:
        bools = []
        for d in days:
            is_night = model.NewBoolVar(f"{team}_d{d}_N")
            model.Add(schedule[(team, d)] == shifts.index('N')).OnlyEnforceIf(is_night)
            model.Add(schedule[(team, d)] != shifts.index('N')).OnlyEnforceIf(is_night.Not())
            bools.append(is_night)
        night_counts.append(sum(bools))
    max_nights = model.NewIntVar(0, num_days, "max_night")
    min_nights = model.NewIntVar(0, num_days, "min_night")
    model.AddMaxEquality(max_nights, night_counts)
    model.AddMinEquality(min_nights, night_counts)
    model.Minimize(max_nights - min_nights)

    # 솔버 설정
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300.0
    solver.parameters.log_search_progress = True
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    # 디버깅 출력
    print(f"솔버 상태: {solver.StatusName(status)}")
    if status == cp_model.INFEASIBLE:
        print("제약 조건 모순. 아래 디버깅 정보 확인:")
        print("1. 최소 3일 Off, 주 40시간, N 후 O/E 금지가 모순될 수 있음.")
        print("2. 팀 수(5개)가 30일 3교대 커버에 충분한지 확인.")
        print("제약 완화 제안: 최소 Off를 2일로 줄이거나, N 후 O만 허용.")

    # JSON 출력
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        result = {}
        for team in team_names:
            calendar = []
            for d in days:
                date_str = (start_date + timedelta(days=d)).strftime('%Y-%m-%d')
                shift = shifts[solver.Value(schedule[(team, d)])]
                calendar.append({
                    "date": date_str,
                    "shift": shift,
                    "members": team_to_people[team]
                })
            result[team] = calendar
        # print(json.dumps(result, ensure_ascii=False, indent=2))
        # 결과를 파일로 저장
        output_path = "./data/time_table.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"[INFO] 시간표가 저장되었습니다: {output_path}")
        print(json.dumps(result, ensure_ascii=False, indent=2))  # 여전히 터미널에도 출력
                
        # 법적 준수 점검
        for team in result:
            off_days = sum(1 for entry in result[team] if entry['shift'] == 'O')
            total_hours = sum(shift_hours[entry['shift']] for entry in result[team])
            print(f"{team}: Off일 = {off_days}, 총 근무시간 = {total_hours}시간")
    else:
        print("해를 찾을 수 없습니다. 로그를 확인하세요.")

# JSON 팀 구성 데이터
team_data = {
    "1조 팀장": "이보은",
    "1조 팀원": ["박주영", "최정환", "문재윤"],
    "2조 팀장": "선서현",
    "2조 팀원": ["박경태", "유희라", "김유범"],
    "3조 팀장": "박서은",
    "3조 팀원": ["김대업", "유예솜", "고준영", "하진영"],
    "4조 팀장": "오장관",
    "4조 팀원": ["윤진영", "한경식", "한현희"],
    "5조 팀장": "정종옥",
    "5조 팀원": ["양성규", "김화백", "이병희"]
}

if __name__ == "__main__":
    create_team_shift_schedule(team_data)