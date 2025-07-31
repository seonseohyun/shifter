from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import os
import json

def create_team_shift_schedule(team_json):
    model = cp_model.CpModel()

    shifts = ['D', 'E', 'N', 'O']  # 교대 종류
    shift_hours = {'D': 8, 'E': 8, 'N': 8, 'O': 0}
    num_days = 30
    days = range(num_days)
    start_date = datetime(2025, 8, 1)
    num_weeks = (num_days + 6) // 7

    # 팀 이름 및 멤버 (이름 + 직급) 구성
    team_names = sorted(set(key.split()[0] for key in team_json if '팀장' in key))
    team_to_people = {}
    staff_id_counter = 101
    for team in team_names:
        members = []
        # 팀장: 직급 team_lead
        members.append({"staff_id": str(staff_id_counter), "이름": team_json[f"{team} 팀장"], "직급": "team_lead"})
        staff_id_counter += 1
        # 팀원: 직급 junior
        for member in team_json[f"{team} 팀원"]:
            members.append({"staff_id": str(staff_id_counter), "이름": member, "직급": "junior"})
            staff_id_counter += 1
        team_to_people[team] = members

    # 변수 생성 (팀별, 일별, 교대 종류)
    # 팀이 하루에 4개 교대 모두 해야 하므로, (팀, 일, 교대) Boolean 변수로 변경
    schedule = {}
    for team in team_names:
        for d in days:
            for s in shifts:
                schedule[(team, d, s)] = model.NewBoolVar(f"{team}_d{d}_{s}")

    # 각 팀과 날짜에 대해 교대 중 하나만 가능
    for team in team_names:
        for d in days:
            model.AddExactlyOne([schedule[(team, d, s)] for s in shifts])

    # 하루에 모든 교대(D, E, N, O)가 적어도 한 팀에 배정되어야 함
    for d in days:
        for s in shifts:
            # 모든 팀 중 하루 해당 교대가 최소 1개 이상 존재
            model.Add(sum(schedule[(team, d, s)] for team in team_names) >= 1)

    # Night 근무 다음날 Off
    for team in team_names:
        for d in range(num_days - 1):
            night = schedule[(team, d, 'N')]
            off_next = schedule[(team, d + 1, 'O')]
            model.AddImplication(night, off_next)

            # N 후 E 금지
            eve_next = schedule[(team, d + 1, 'E')]
            # night + eve_next <=1  (즉, N 다음날 E 불가)
            model.AddBoolOr([night.Not(), eve_next.Not()])

    # 전체 기간 최소 3일 Off (완화 가능)
    for team in team_names:
        model.Add(sum(schedule[(team, d, 'O')] for d in days) >= 3)

    # 주 40시간 초과 금지
    for team in team_names:
        for w in range(num_weeks):
            week_start = w * 7
            week_end = min(week_start + 7, num_days)
            hours = []
            for d in range(week_start, week_end):
                for s in shifts:
                    hours.append(schedule[(team, d, s)] * shift_hours[s])
            model.Add(sum(hours) <= 40)

    # Night 근무 균형화 목적
    night_counts = []
    for team in team_names:
        night_counts.append(sum(schedule[(team, d, 'N')] for d in days))
    max_nights = model.NewIntVar(0, num_days, "max_night")
    min_nights = model.NewIntVar(0, num_days, "min_night")
    model.AddMaxEquality(max_nights, night_counts)
    model.AddMinEquality(min_nights, night_counts)
    model.Minimize(max_nights - min_nights)

    # 솔버 실행
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300.0
    solver.parameters.log_search_progress = True
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    print(f"솔버 상태: {solver.StatusName(status)}")
    if status == cp_model.INFEASIBLE:
        print("제약 조건 모순 발생")

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        result = {}
        for d in days:
            date_str = (start_date + timedelta(days=d)).strftime('%Y-%m-%d')
            day_schedule = []
            for s in shifts:
                # 해당 교대에 배정된 팀 찾기
                assigned_teams = []
                for team in team_names:
                    if solver.Value(schedule[(team, d, s)]) == 1:
                        assigned_teams.append({
                            "팀명": team,
                            "members": team_to_people[team]
                        })
                day_schedule.append({
                    "shift": s,
                    "teams": assigned_teams
                })
            result[date_str] = day_schedule

        output_path = "./data/time_table.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"[INFO] 시간표가 저장되었습니다: {output_path}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("해를 찾을 수 없습니다.")


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
