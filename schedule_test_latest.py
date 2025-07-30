from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import pandas as pd
import os
import json

# ======================
# 🔧 사용자 설정
# ======================

# 1. 교대 입력 (예: ["D", "E", "N", "O"])
shift_labels = ["D", "E", "N", "O"]

# 2. 팀 구성 정보 (직급 포함)
team_data = {
    "1조": {
        "팀원": [
            {"이름": "이보은", "직급": "senior"},
            {"이름": "박주영", "직급": "junior"},
            {"이름": "최정환", "직급": "junior"},
            {"이름": "문재윤", "직급": "junior"},
        ]
    },
    "2조": {
        "팀원": [
            {"이름": "선서현", "직급": "senior"},
            {"이름": "박경태", "직급": "junior"},
            {"이름": "유희라", "직급": "junior"},
            {"이름": "김유범", "직급": "junior"},
        ]
    },
    "3조": {
        "팀원": [
            {"이름": "박서은", "직급": "team_lead"},
            {"이름": "김대업", "직급": "junior"},
            {"이름": "유예솜", "직급": "junior"},
            {"이름": "고준영", "직급": "junior"},
            {"이름": "하진영", "직급": "junior"},
        ]
    },
    "4조": {
        "팀원": [
            {"이름": "오장관", "직급": "team_lead"},
            {"이름": "윤진영", "직급": "junior"},
            {"이름": "한경식", "직급": "junior"},
            {"이름": "한현희", "직급": "junior"},
        ]
    },
    "5조": {
        "팀원": [
            {"이름": "정종옥", "직급": "team_lead"},
            {"이름": "양성규", "직급": "junior"},
            {"이름": "김화백", "직급": "junior"},
            {"이름": "이병희", "직급": "junior"},
        ]
    }
}

# 3. 시작 날짜 및 기간
start_date = datetime(2025, 8, 1)
num_days = 30

# ======================
# 🧠 알고리즘 시작
# ======================

def create_schedule_console():
    model = cp_model.CpModel()
    days = range(num_days)
    shift_index = {s: i for i, s in enumerate(shift_labels)}
    team_names = list(team_data.keys())

    # 이름+직급 포함
    team_to_people_info = {
        team: [
            {"이름": member["이름"], "직급": member["직급"]}
            for member in team_data[team]["팀원"]
        ]
        for team in team_data
    }

    # 변수 생성
    schedule = {}
    for team in team_data:
        for d in days:
            schedule[(team, d)] = model.NewIntVar(0, len(shift_labels) - 1, f"{team}_day{d}")

    # 최소 하루 이상 근무 보장
    for d in days:
        for s in shift_labels:
            daily_bools = []
            for team in team_data:
                b = model.NewBoolVar(f"{team}_{d}_{s}")
                model.Add(schedule[(team, d)] == shift_index[s]).OnlyEnforceIf(b)
                model.Add(schedule[(team, d)] != shift_index[s]).OnlyEnforceIf(b.Not())
                daily_bools.append(b)
            model.AddBoolOr(daily_bools)

    # ❗ 2일 초과 연속 야간 금지
    if "N" in shift_labels:
        idx_N = shift_index["N"]
        for team in team_data:
            for d in range(num_days - 2):
                b0 = model.NewBoolVar("")
                b1 = model.NewBoolVar("")
                b2 = model.NewBoolVar("")
                model.Add(schedule[(team, d)] == idx_N).OnlyEnforceIf(b0)
                model.Add(schedule[(team, d)] != idx_N).OnlyEnforceIf(b0.Not())
                model.Add(schedule[(team, d+1)] == idx_N).OnlyEnforceIf(b1)
                model.Add(schedule[(team, d+1)] != idx_N).OnlyEnforceIf(b1.Not())
                model.Add(schedule[(team, d+2)] == idx_N).OnlyEnforceIf(b2)
                model.Add(schedule[(team, d+2)] != idx_N).OnlyEnforceIf(b2.Not())
                model.AddBoolOr([b0.Not(), b1.Not(), b2.Not()])

    # 야간 근무 균형화 목적
    night_counts = []
    if "N" in shift_labels:
        idx_N = shift_index["N"]
        for team in team_data:
            bools = []
            for d in days:
                b = model.NewBoolVar("")
                model.Add(schedule[(team, d)] == idx_N).OnlyEnforceIf(b)
                model.Add(schedule[(team, d)] != idx_N).OnlyEnforceIf(b.Not())
                bools.append(b)
            night_counts.append(sum(bools))
        max_n = model.NewIntVar(0, num_days, "")
        min_n = model.NewIntVar(0, num_days, "")
        model.AddMaxEquality(max_n, night_counts)
        model.AddMinEquality(min_n, night_counts)
        model.Minimize(max_n - min_n)

    # 솔버 실행
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    status = solver.Solve(model)

    if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print("❌ 해를 찾을 수 없습니다.")
        return

    # ✅ 날짜별 전체 팀 출력
    result_by_date = []
    for d in days:
        date_str = (start_date + timedelta(days=d)).strftime('%Y-%m-%d')
        teams_for_day = []
        for team in team_names:
            shift = shift_labels[solver.Value(schedule[(team, d)])]
            members = team_to_people_info[team]
            teams_for_day.append({
                "team": team,
                "shift": shift,
                "members": members
            })
        result_by_date.append({
            "date": date_str,
            "teams": teams_for_day
        })

    # 파일 저장
    output_path = "./data/time_table.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_by_date, f, ensure_ascii=False, indent=2)

    print(f"[INFO] 시간표가 저장되었습니다: {output_path}")
    print(json.dumps(result_by_date, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    create_schedule_console()
