from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import json

def create_team_shift_schedule(team_json):
    model = cp_model.CpModel()

    # 설정
    shifts = ['D', 'E', 'N', 'O']  # Day, Evening, Night, Off
    num_days = 30  # 원하는 일수
    days = range(num_days)
    start_date = datetime(2025, 8, 1)  # 시작 날짜

    # 조 이름 및 인원 정리
    team_names = sorted(set(key.split()[0] for key in team_json if '팀장' in key))
    team_to_people = {
        team: [team_json[f"{team} 팀장"]] + team_json[f"{team} 팀원"]
        for team in team_names
    }

    # 변수 생성: 팀 단위로 근무 배정
    schedule = {}
    for team in team_names:
        for d in days:
            schedule[(team, d)] = model.NewIntVar(0, len(shifts) - 1, f"{team}_day{d}")

    # 제약 1: 각 조는 매일 D, E, N 중 하나를 선택 (팀 단위로 동일 근무)
    for d in days:
        for s in ['D', 'E', 'N']:
            shift_bools = []
            for team in team_names:
                is_shift = model.NewBoolVar(f"{team}_d{d}_{s}")
                model.Add(schedule[(team, d)] == shifts.index(s)).OnlyEnforceIf(is_shift)
                model.Add(schedule[(team, d)] != shifts.index(s)).OnlyEnforceIf(is_shift.Not())
                shift_bools.append(is_shift)
            model.Add(sum(shift_bools) >= 1)

    # 제약 2: Night 근무 다음 날 Off 또는 Evening (팀 단위)
    for team in team_names:
        for d in range(num_days - 1):
            night = model.NewBoolVar(f"{team}_d{d}_isN")
            model.Add(schedule[(team, d)] == shifts.index('N')).OnlyEnforceIf(night)
            model.Add(schedule[(team, d)] != shifts.index('N')).OnlyEnforceIf(night.Not())

            next_ok = model.NewBoolVar(f"{team}_d{d+1}_isOE")
            model.AddAllowedAssignments(
                [schedule[(team, d + 1)]],
                [[shifts.index('O')], [shifts.index('E')]]
            ).OnlyEnforceIf(next_ok)
            model.AddForbiddenAssignments(
                [schedule[(team, d + 1)]],
                [[shifts.index('D')], [shifts.index('N')]]
            ).OnlyEnforceIf(next_ok)
            model.AddImplication(night, next_ok)

    # 제약 3: Night 근무 균형 (팀 단위)
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

    # 사용자 정의 고정 근무 제약 조건 목록
    custom_constraints = [
        ("2조", "2025-08-09", "O"),
        ("4조", "2025-08-13", "D"),
    ]

    for team, date_str, shift_code in custom_constraints:
        day_index = (datetime.strptime(date_str, "%Y-%m-%d") - start_date).days
        if 0 <= day_index < num_days:
            model.Add(schedule[(team, day_index)] == shifts.index(shift_code))
        else:
            print(f"⚠️ 날짜 {date_str}는 근무 범위에 포함되지 않음 (건너뜀)")

    # 솔버 설정
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0
    status = solver.Solve(model)

    # JSON 출력: 팀 단위로 캘린더 형태
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
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("해를 찾을 수 없습니다.")

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
    "5조 팀장":"정종옥",
    "5조 팀원": ["양성규",  "김화백", "이병희"]
}

if __name__ == "__main__":
    create_team_shift_schedule(team_data)