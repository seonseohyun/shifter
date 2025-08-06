import socket
import json
from datetime import datetime, timedelta
import calendar
from ortools.sat.python import cp_model
import os

HOST = '127.0.0.1'
PORT = 6002

# 직군별 제약조건 정의
POSITION_RULES = {
    "간호": {
        "min_off_days": 3,
        "newbie_no_night": True,
        "night_after_off": True,
        "max_weekly_hours": 60,
        "max_monthly_hours": 190,
        "newbie_grade": 5,  # 신규간호사 등급
        "shifts": ['D', 'E', 'N', 'O'],  # 3교대
        "shift_hours": {'D': 8, 'E': 8, 'N': 8, 'O': 0}
    },
    "소방": {
        "shift_cycle": "D24-O-O",
        "duty_per_cycle": 1,
        "night_after_off": True,
        "max_weekly_hours": 72,
        "max_monthly_hours": 190,
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

def parse_target_month(target_month):
    """target_month 파싱하여 시작일과 일수 계산"""
    try:
        if target_month:
            year, month = map(int, target_month.split('-'))
        else:
            # 기본값: 현재 월
            now = datetime.now()
            year, month = now.year, now.month
        
        # 해당 월의 첫째 날과 마지막 날 계산
        start_date = datetime(year, month, 1)
        num_days = calendar.monthrange(year, month)[1]  # 해당 월의 일수
        
        print(f"[INFO] 대상 월: {year}년 {month}월 ({num_days}일)")
        return start_date, num_days
        
    except Exception as e:
        print(f"[ERROR] target_month 파싱 오류: {e}")
        # 기본값: 2025년 8월
        return datetime(2025, 8, 1), 31

def apply_position_constraints(model, schedule, person, days, shifts, shift_hours, num_weeks, rules, position, night_shifts):
    """직군별 제약조건 적용"""
    sid = str(person["staff_id"])
    grade = person.get("grade", 1)
    name = person.get("name", f"staff_{sid}")
    
    print(f"[INFO] {name} ({position}) 제약조건 적용 중...")
    
    if position == "간호":
        # 신규간호사는 야간 근무 금지
        # if rules.get("newbie_no_night", False) and grade == rules.get("newbie_grade", 5):
        #     if 'N' in shifts:
        #         for d in days:
        #             model.Add(schedule[(sid, d, 'N')] == 0)
        #         print(f"[INFO] {name}: 신규간호사 야간 근무 금지 적용")
        
        #이제 다양한 night근무 키워드를 보고 신규간호사는 야간 배제를 한다.
        if rules.get("newbie_no_night", False) and grade == rules.get("newbie_grade", 5):
            for ns in night_shifts:
                if ns in shifts:
                    for d in days:
                        model.Add(schedule[(sid, d, ns)] == 0)
            if night_shifts:
                print(f"[INFO] {name}: 신규간호사 야간 근무 금지 적용 (대상 시프트: {night_shifts})")
        
        
        #야간 근무 후 반드시 휴무
        if rules.get("night_after_off", False) and 'O' in shifts:
            for ns in night_shifts:
                if ns in shifts:
                    for d in range(len(days) -1):
                        night = schedule[(sid, d, ns)]
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
    base_monthly_hours = person.get("total_monthly_work_hours", rules.get("max_monthly_hours", 190)) # 법정최고 209
    max_monthly_hours = int(base_monthly_hours * 1.1)  # 10% 여유분
    min_monthly_hours = base_monthly_hours - 20  # 최대 근무시간에서 -20시간

    monthly_hours = sum(schedule[(sid, d, s)] * shift_hours[s] for d in days for s in shifts)
    # 상한 및 하한 constraint 적용
    model.Add(monthly_hours <= max_monthly_hours)
    model.Add(monthly_hours >= min_monthly_hours)
    
    print(f"[INFO] {name}: 주당 최대 {max_weekly_hours}시간, 월 {min_monthly_hours}-{max_monthly_hours}시간 (목표: {base_monthly_hours}시간)")

def validate_request_parameters(staff_data, shift_type, position, custom_rules):
    """요청 매개변수 검증 및 상세 오류 메시지 생성"""
    errors = []
    warnings = []
    
    # 1. 직원 데이터 검증
    if not staff_data or "staff" not in staff_data:
        errors.append("유효한 staff_data가 필요합니다. staff_data.staff 배열이 누락되었습니다.")
        return errors, warnings
    
    staff_list = staff_data["staff"]
    if not staff_list or len(staff_list) == 0:
        errors.append("최소 1명 이상의 직원 데이터가 필요합니다.")
        return errors, warnings
    
    if len(staff_list) < 5:
        warnings.append(f"직원 수가 {len(staff_list)}명으로 적습니다. 최소 10-15명을 권장합니다.")
    
    # 2. 직원 정보 검증
    required_fields = ["name", "staff_id", "grade", "position", "total_monthly_work_hours"]
    for i, staff in enumerate(staff_list):
        for field in required_fields:
            if field not in staff:
                errors.append(f"직원 {i+1}번의 필수 필드 '{field}'가 누락되었습니다.")
        
        # 근무시간 검증
        if "total_monthly_work_hours" in staff:
            hours = staff["total_monthly_work_hours"]
            if not isinstance(hours, (int, float)) or hours < 100 or hours > 250:
                errors.append(f"직원 '{staff.get('name', f'{i+1}번')}'의 월 근무시간 {hours}가 비현실적입니다. (100-250시간 권장)")
    
    # 3. custom_rules 검증
    if custom_rules:
        if "shifts" not in custom_rules or "shift_hours" not in custom_rules:
            errors.append("custom_rules에는 'shifts'와 'shift_hours' 필드가 모두 필요합니다.")
        else:
            shifts = custom_rules["shifts"]
            shift_hours = custom_rules["shift_hours"]
            
            # 시프트 개수 검증
            if len(shifts) < 2:
                errors.append(f"최소 2개 이상의 시프트가 필요합니다. 현재: {len(shifts)}개")
            elif len(shifts) > 6:
                errors.append(f"시프트 개수가 {len(shifts)}개로 너무 많습니다. 최대 6개까지 권장합니다.")
            
            # 휴무 시프트 검증
            off_shifts = [s for s in shifts if s in ['O', 'Off', 'REST', '휴무', '쉼', 'Free']]
            if len(off_shifts) == 0:
                errors.append("휴무 시프트가 없습니다. 'O', 'Off', 'REST', '휴무', '쉼' 중 하나를 포함해야 합니다.")
            
            # 시간 배정 검증
            for shift in shifts:
                if shift not in shift_hours:
                    errors.append(f"시프트 '{shift}'에 대한 시간 배정이 누락되었습니다.")
                else:
                    hours = shift_hours[shift]
                    if shift in off_shifts and hours != 0:
                        errors.append(f"휴무 시프트 '{shift}'의 시간은 0이어야 합니다. 현재: {hours}시간")
                    elif shift not in off_shifts and (hours < 4 or hours > 24):
                        errors.append(f"근무 시프트 '{shift}'의 시간 {hours}가 비현실적입니다. (4-24시간 권장)")
            
            # 수학적 타당성 검증
            work_shifts = [s for s in shifts if s not in off_shifts]
            if work_shifts:
                daily_max_hours = sum(shift_hours.get(s, 0) for s in work_shifts)
                monthly_max_hours = daily_max_hours * 30
                avg_target_hours = sum(staff.get("total_monthly_work_hours", 180) for staff in staff_list) / len(staff_list)
                
                if daily_max_hours < 18:
                    warnings.append(f"하루 최대 근무시간이 {daily_max_hours}시간으로 부족할 수 있습니다. 18시간 이상 권장합니다.")
                
                # 15명 기준으로 4교대 이상 시 경고
                if len(work_shifts) >= 4 and len(staff_list) <= 15:
                    warnings.append(f"{len(work_shifts)}교대 시스템은 {len(staff_list)}명으로 운영하기 어려울 수 있습니다. 최소 20명 이상을 권장합니다.")
                
                # 시간당 근무시간이 너무 적을 때
                min_shift_hours = min(shift_hours.get(s, 0) for s in work_shifts if shift_hours.get(s, 0) > 0)
                if min_shift_hours < 6:
                    warnings.append(f"최소 시프트 시간이 {min_shift_hours}시간으로 너무 짧습니다. 6시간 이상을 권장합니다.")
    
    return errors, warnings

def create_individual_shift_schedule(staff_data, shift_type, position="default", target_month=None, custom_rules=None):
    """개별 직원 근무표 생성 (상세한 오류 처리 포함)"""
    
    # 1. 요청 매개변수 사전 검증
    validation_errors, validation_warnings = validate_request_parameters(staff_data, shift_type, position, custom_rules)
    
    if validation_errors:
        return {
            "result": "생성실패",
            "reason": "입력 매개변수 오류: " + "; ".join(validation_errors),
            "warnings": validation_warnings if validation_warnings else None
        }
    
    if validation_warnings:
        print(f"[WARNING] 검증 경고사항: {'; '.join(validation_warnings)}")
    
    try:
        model = cp_model.CpModel()
        
        # 기본 규칙 가져오기
        base_rules = POSITION_RULES.get(position, POSITION_RULES["default"])

        #야간 시프트 동적식별 2교대 'B','Late'
        night_keywords = ['n', 'night','야간','Night','B','Late','밤','22-06','Shift3','Gamma','Delta','ShortNight']
        night_shifts = []

        if custom_rules and "night_shifts" in custom_rules:
            night_shifts = custom_rules["night_shifts"]
        else:
            for s in shifts:
                if any(keyword.lower() in s.lower() for keyword in night_keywords):
                    night_shifts.append(s)
        if not night_shifts:
            print(f"[info] 야간 시프트가 식별되지 않음 (직군 {position})")
        else:
            print(f"[info] 식별된 야간 시프트 : {night_shifts}")

        # custom_rules에서 shifts와 shift_hours만 추출하여 적용 (다른 제약조건은 무시)
        if custom_rules and "shifts" in custom_rules and "shift_hours" in custom_rules:
            shifts = custom_rules["shifts"]
            shift_hours = custom_rules["shift_hours"]
            night_shift = 'N' if 'N' in shifts else None
            print(f"[INFO] 커스텀 시프트 적용: {shifts}")
            
            # custom_rules의 다른 항목들은 무시됨을 알림 (shifts, shift_hours만 오버라이드)
            ignored_keys = set(custom_rules.keys()) - {"shifts", "shift_hours"}
            if ignored_keys:
                print(f"[INFO] 기본 제약조건 유지, 오버라이드된 항목: shifts, shift_hours")
        elif position in POSITION_RULES:
            shifts = base_rules["shifts"]
            shift_hours = base_rules["shift_hours"]
            night_shift = 'N' if 'N' in shifts else None
        else:
            # 기존 로직 유지 (호환성)
            if shift_type not in [2, 3, 4]:
                return {
                    "result": "생성실패",
                    "reason": f"지원되지 않는 shift_type: {shift_type}. 2, 3, 4만 지원됩니다."
                }
                
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
        
        # 동적 날짜 계산
        start_date, num_days = parse_target_month(target_month)
        days = range(num_days)
        num_weeks = (num_days + 6) // 7

        all_people = staff_data["staff"]

        unique_grades = set(person["grade"] for person in all_people)
        if len(unique_grades) > 5:
            return {
                "result": "생성실패",
                "reason": f"지원되지 않는 등급 수: {len(unique_grades)}개. 최대 5개 등급까지 지원됩니다."
            }

        schedule = {}
        for person in all_people:
            sid = str(person["staff_id"])
            for d in days:
                for s in shifts:
                    # 불린변수를생성 : 해당직원이 해당날짜에 해당 shift를 배정받았는지(1) or (0)
                    #sid 직원 d 날짜 s deno중 하나
                    schedule[(sid, d, s)] = model.NewBoolVar(f"{sid}_d{d}_{s}")    

        for person in all_people:
            sid = str(person["staff_id"])
            for d in days:
                #각 직원별로 매일 정확히 하나의 shift를 배정
                model.AddExactlyOne([schedule[(sid, d, s)] for s in shifts])

        # 각 교대에 최소 인원 보장 (오프 제외)
        for d in days:
            for s in shifts:
                if s != 'O':
                    #각 날짜와 비휴무 shift에 최소 1명의 직원을 배정한다.
                    model.Add(sum(schedule[(str(person["staff_id"]), d, s)] for person in all_people) >= 2)

        # 직군별 제약조건 적용 (고정된 기본 규칙 사용)
        for person in all_people:
            # 개별 직원의 position 우선, 없으면 전체 position 사용
            person_position = person.get("position", position)  
            person_rules = POSITION_RULES.get(person_position, base_rules)

            apply_position_constraints(model, schedule, person, days, shifts, shift_hours, num_weeks, person_rules, person_position, night_shifts)

        # 야간 근무 균등 분배 (야간 근무가 있는 경우만 소방은 24시간)
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
        solver.parameters.max_time_in_seconds = 20.0  # 시간을 20초로 단축
        solver.parameters.log_search_progress = False  # 로그 비활성화
        solver.parameters.num_search_workers = 1  # 단일 워커로 오버헤드 최소화
        solver.parameters.cp_model_presolve = True  # 전처리 활성화 유지
        status = solver.Solve(model)

        print(f"솔버 상태: {solver.StatusName(status)}")
        print(f"해결 시간: {solver.WallTime():.2f}초")

        # 솔버 실패 시 상세한 오류 메시지 생성
        if status == cp_model.INFEASIBLE:
            return {
                "result": "생성실패",
                "reason": f"제약조건을 만족하는 해가 존재하지 않습니다. 다음을 확인해보세요: 1) 직원 수({len(all_people)}명)가 시프트를 채우기 충분한지, 2) 월 근무시간 목표가 현실적인지, 3) 시프트 시간 배정이 적절한지",
                "details": {
                    "solver_status": solver.StatusName(status),
                    "solve_time": f"{solver.WallTime():.2f}초",
                    "staff_count": len(all_people),
                    "shifts": shifts,
                    "shift_hours": shift_hours,
                    "days_in_month": num_days
                }
            }
        elif status == cp_model.MODEL_INVALID:
            return {
                "result": "생성실패", 
                "reason": "모델 정의에 오류가 있습니다. 입력 데이터의 유효성을 확인해주세요.",
                "details": {"solver_status": solver.StatusName(status)}
            }
        elif status == cp_model.UNKNOWN:
            return {
                "result": "생성실패",
                "reason": f"시간 초과({solver.parameters.max_time_in_seconds}초) 또는 메모리 부족으로 해를 찾지 못했습니다. 제약조건을 완화하거나 직원 수를 늘려보세요.",
                "details": {
                    "solver_status": solver.StatusName(status),
                    "solve_time": f"{solver.WallTime():.2f}초"
                }
            }

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            if night_shift and night_shift in shifts:
                night_balance_value = solver.Value(max_nights) - solver.Value(min_nights)
                print(f"야간 근무 균등성: {night_balance_value}")
                print(f"최대 야간 근무: {solver.Value(max_nights)}회, 최소 야간 근무: {solver.Value(min_nights)}회")
            else:
                print("야간 근무 없음 - 균등성 체크 생략")

    except Exception as e:
        return {
            "result": "생성실패",
            "reason": f"근무표 생성 중 예상치 못한 오류가 발생했습니다: {str(e)}",
            "details": {"error_type": type(e).__name__}
        }
    
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
        # 이미 위에서 상세한 오류 메시지를 반환했으므로 여기 도달하지 않음
        return {
            "result": "생성실패",
            "reason": f"알 수 없는 솔버 상태: {solver.StatusName(status) if 'solver' in locals() else '솔버 초기화 실패'}"
        }

def handle_request(request_json):
    try:
        data = json.loads(request_json)
        staff_data = data.get("staff_data")
        shift_type = data.get("shift_type", 3)
        position = data.get("position", "default")  # 직군 정보 추가
        target_month = data.get("target_month")  # 대상 월 정보 추가

        if not staff_data or "staff" not in staff_data:
            return json.dumps({
                "result": "생성실패",
                "reason": "유효한 staff_data가 필요합니다. staff_data.staff 배열이 누락되었습니다."
            }, ensure_ascii=False)

        custom_rules = data.get("custom_rules")  # 최상위에서 custom_rules 추출
        
        # custom_rules 로깅
        if custom_rules:
            print(f"[INFO] 커스텀 규칙 감지: {custom_rules}")
        
        print(f"[INFO] 요청 받음 - 직군: {position}, 직원 수: {len(staff_data['staff'])}, 대상 월: {target_month}")
        result = create_individual_shift_schedule(staff_data, shift_type, position, target_month, custom_rules)

        # result가 딕셔너리이고 "result" 키를 가지고 있으면 실패 응답
        if isinstance(result, dict) and result.get("result") == "생성실패":
            return json.dumps(result, ensure_ascii=False)
        elif result is None:
            return json.dumps({
                "result": "생성실패", 
                "reason": "알 수 없는 오류로 근무표 생성에 실패했습니다."
            }, ensure_ascii=False)
        else:
            return json.dumps({"status": "ok", "schedule": result}, ensure_ascii=False)

    except json.JSONDecodeError as e:
        return json.dumps({
            "result": "생성실패",
            "reason": f"JSON 파싱 오류: {str(e)}. 요청 데이터 형식을 확인해주세요."
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "result": "생성실패",
            "reason": f"서버 내부 오류: {str(e)}",
            "details": {"error_type": type(e).__name__}
        }, ensure_ascii=False)

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
