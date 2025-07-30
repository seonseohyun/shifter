from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import json

def create_team_shift_schedule(team_json):
    model = cp_model.CpModel()

    # 설정
    shifts = ['D', 'E', 'N', 'O']  # Day, Evening, Night, Off
    shift_times = {  # 시작/종료 시간 (datetime.time 객체, 24시간제)
        'D': (datetime.strptime('09:00', '%H:%M').time(), datetime.strptime('17:00', '%H:%M').time()),
        'E': (datetime.strptime('14:00', '%H:%M').time(), datetime.strptime('22:00', '%H:%M').time()),
        'N': (datetime.strptime('22:00', '%H:%M').time(), datetime.strptime('06:00', '%H:%M').time()),  # 다음 날 종료
        'O': (None, None)  # 휴식
    }
    shift_hours = {'D': 8, 'E': 8, 'N': 8, 'O': 0}  # 각 교대 근무시간 (휴게 제외)
    num_days = 30
    days = range(num_days)
    start_date = datetime(2025, 8, 1)
    num_weeks = (num_days + 6) // 7  # 대략적인 주 수

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

    # 제약 2: Night 근무 다음 날 Off 또는 Evening, 그리고 11시간 휴식 강화
    for team in team_names:
        for d in range(num_days - 1):
            night = model.NewBoolVar(f"{team}_d{d}_isN")
            model.Add(schedule[(team, d)] == shifts.index('N')).OnlyEnforceIf(night)
            model.Add(schedule[(team, d)] != shifts.index('N')).OnlyEnforceIf(night.Not())

            # 다음 날 허용: O 또는 E
            model.Add(schedule[(team, d + 1)] == shifts.index('O')).OnlyEnforceIf(night)
            model.Add(schedule[(team, d + 1)] == shifts.index('E')).OnlyEnforceIf(night)
            # N 후 D/N 금지 이미 포함

    # 새 제약: 근로일 간 최소 11시간 휴식 (모든 교대에 적용)
    for team in team_names:
        for d in range(num_days - 1):
            for s1 in shifts[:-1]:  # O 제외
                for s2 in shifts[:-1]:  # O 제외
                    is_s1 = model.NewBoolVar(f"{team}_d{d}_{s1}")
                    model.Add(schedule[(team, d)] == shifts.index(s1)).OnlyEnforceIf(is_s1)
                    model.Add(schedule[(team, d)] != shifts.index(s1)).OnlyEnforceIf(is_s1.Not())
                    is_s2 = model.NewBoolVar(f"{team}_d{d+1}_{s2}")
                    model.Add(schedule[(team, d + 1)] == shifts.index(s2)).OnlyEnforceIf(is_s2)
                    model.Add(schedule[(team, d + 1)] != shifts.index(s2)).OnlyEnforceIf(is_s2.Not())

                    # 종료 시간과 다음 시작 시간 비교 (시간 차 계산)
                    end_time1 = shift_times[s1][1]
                    start_time2 = shift_times[s2][0]
                    # N처럼 다음 날 종료 시 +24시간 고려
                    if end_time1 < shift_times[s1][0]:  # 밤을 넘는 경우 (N)
                        end_dt = datetime(2000, 1, 2, end_time1.hour, end_time1.minute)  # 다음 날
                    else:
                        end_dt = datetime(2000, 1, 1, end_time1.hour, end_time1.minute)
                    start_dt = datetime(2000, 1, 1, start_time2.hour, start_time2.minute)
                    if start_dt < end_dt:
                        start_dt += timedelta(days=1)  # 다음 날 시작
                    rest_hours = (start_dt - end_dt).total_seconds() / 3600
                    if rest_hours < 11:
                        model.Add(is_s1 + is_s2 <= 1)  # 둘 다 참이면 금지

    # 새 제약: 주휴일 - 매주 최소 1일 O
    for team in team_names:
        for w in range(num_weeks):
            week_start = w * 7
            week_end = min(week_start + 7, num_days)
            off_bools = []
            for d in range(week_start, week_end):
                is_off = model.NewBoolVar(f"{team}_w{w}_d{d}_O")
                model.Add(schedule[(team, d)] == shifts.index('O')).OnlyEnforceIf(is_off)
                model.Add(schedule[(team, d)] != shifts.index('O')).OnlyEnforceIf(is_off.Not())
                off_bools.append(is_off)
            model.Add(sum(off_bools) >= 1)

    # 새 제약: 주 40시간 초과 금지
    for team in team_names:
        for w in range(num_weeks):
            week_start = w * 7
            week_end = min(week_start + 7, num_days)
            hours_var = model.NewIntVar(0, 100, f"{team}_w{w}_hours")  # 임시 변수
            hour_terms = []
            for d in range(week_start, week_end):
                for s in shifts:
                    is_s = model.NewBoolVar(f"{team}_d{d}_{s}")
                    model.Add(schedule[(team, d)] == shifts.index(s)).OnlyEnforceIf(is_s)
                    model.Add(schedule[(team, d)] != shifts.index(s)).OnlyEnforceIf(is_s.Not())
                    hour_terms.append(is_s * shift_hours[s])
            model.Add(sum(hour_terms) == hours_var)
            model.Add(hours_var <= 40)

    # 제약 3: Night 근무 균형 (기존 유지)
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

    # 사용자 정의 고정 근무 제약 조건 목록 (기존 유지)
    custom_constraints = [
        ("2조", "2025-08-09", "O"),
        ("4조", "2025-08-13", "D"),
    ]

    for team, date_str, shift_code in custom_constraints:
        day_index = (datetime.strptime(date_str, "%Y-%m-%d") -