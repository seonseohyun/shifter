#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def debug_shift_detection():
    """시프트 식별 로직 디버깅"""
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "3교대 영문 시스템", 
            "shifts": ['Morning', 'Evening', 'Night', 'Off'],
            "shift_hours": {'Morning': 8, 'Evening': 8, 'Night': 8, 'Off': 0}
        },
        {
            "name": "3교대 축약형",
            "shifts": ['M', 'A', 'N', 'R'], 
            "shift_hours": {'M': 8, 'A': 8, 'N': 8, 'R': 0}
        }
    ]
    
    for case in test_cases:
        shifts = case["shifts"]
        shift_hours = case["shift_hours"]
        
        print(f"\n{'='*60}")
        print(f"테스트: {case['name']}")
        print(f"시프트 목록: {shifts}")
        print(f"시프트 시간: {shift_hours}")
        
        test_single_case(shifts, shift_hours)

def test_single_case(shifts, shift_hours):
    
    # 야간 시프트 식별 (수정된 로직)
    night_keywords = ['night', '야간', '밤', '22-06', 'nocturnal']  # 'n' 제거
    night_shifts = []
    
    print(f"\n야간 키워드: {night_keywords}")
    for s in shifts:
        matches = []
        # 수정된 매칭 로직
        if (s.lower() == 'n' or  # 정확히 'N' 시프트
            any(keyword.lower() == s.lower() for keyword in night_keywords) or  # 완전 매칭
            any(keyword.lower() in s.lower() and len(keyword) > 2 for keyword in night_keywords)):  # 3글자 이상만 부분 매칭
            if s.lower() == 'n':
                matches.append("정확히 'N'")
            matches.extend([kw for kw in night_keywords if kw.lower() == s.lower()])
            matches.extend([kw for kw in night_keywords if kw.lower() in s.lower() and len(kw) > 2])
            night_shifts.append(s)
            print(f"  '{s}' → 야간 시프트 (매칭: {matches})")
        else:
            print(f"  '{s}' → 야간 시프트 아님")
    
    # 휴무 시프트 식별 (수정된 로직)
    off_keywords = ['off', 'rest', '휴무', '쉼', 'free']  # 'o' 제거
    off_shifts = []
    
    print(f"\n휴무 키워드: {off_keywords}")
    for s in shifts:
        matches = []
        # 수정된 매칭 로직
        if (s.lower() in ['o', 'r'] or  # 정확히 'O', 'R' 시프트
            any(keyword.lower() == s.lower() for keyword in off_keywords) or  # 완전 매칭
            any(keyword.lower() in s.lower() and len(keyword) > 2 for keyword in off_keywords)):  # 3글자 이상만 부분 매칭
            if s.lower() in ['o', 'r']:
                matches.append(f"정확히 '{s.upper()}'")
            matches.extend([kw for kw in off_keywords if kw.lower() == s.lower()])
            matches.extend([kw for kw in off_keywords if kw.lower() in s.lower() and len(kw) > 2])
            off_shifts.append(s)
            print(f"  '{s}' → 휴무 시프트 (매칭: {matches})")
        else:
            print(f"  '{s}' → 휴무 시프트 아님")
    
    print(f"\n최종 결과:")
    print(f"야간 시프트: {night_shifts}")
    print(f"휴무 시프트: {off_shifts}")
    
    # 계산 확인
    work_shifts = [s for s in shifts if s not in off_shifts]
    daily_max_hours = sum(shift_hours.get(s, 0) for s in work_shifts)
    
    print(f"\n계산 결과:")
    print(f"근무 시프트: {work_shifts}")
    print(f"하루 최대 근무시간: {daily_max_hours}시간")
    print(f"예상값: 24시간 (Morning 8 + Evening 8 + Night 8)")
    
    if daily_max_hours != 24:
        print("❌ 계산 오류 발견!")
        for s in shifts:
            in_work = s in work_shifts
            in_off = s in off_shifts
            hours = shift_hours.get(s, 0)
            print(f"  {s}: {hours}h, 근무시프트={in_work}, 휴무시프트={in_off}")
    else:
        print("✅ 계산 정상")

if __name__ == "__main__":
    debug_shift_detection()