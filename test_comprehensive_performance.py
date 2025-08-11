#!/usr/bin/env python3
"""
종합 성능 및 형평성 테스트 시스템
- 10명~30명 규모별 테스트
- 3교대~5교대 시스템 테스트  
- 처리 시간, 제약조건 준수, 형평성 종합 분석
"""

import socket
import struct
import json
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import statistics
from collections import defaultdict

class ComprehensivePerformanceTest:
    def __init__(self, host: str = "localhost", port: int = 6004):
        self.host = host
        self.port = port
        self.test_results = []
    
    def generate_staff_data(self, count: int, position: str = "간호") -> List[Dict[str, Any]]:
        """지정된 수의 직원 데이터를 생성합니다."""
        staff_data = []
        
        names = [
            "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
            "한", "오", "서", "신", "권", "황", "안", "송", "류", "전",
            "진", "노", "하", "홍", "배", "성", "백", "전", "고", "문"
        ]
        
        # 현실적인 직급 분포
        if count <= 10:
            grades = [3] * (count // 3) + [2] * (count // 2) + [1] * (count - count//3 - count//2)
        elif count <= 20:
            grades = [3] * (count // 4) + [2] * (count // 2) + [1] * (count - count//4 - count//2) + [5] * (count // 10)
        else:
            grades = [3] * (count // 5) + [2] * (count // 3) + [1] * (count // 3) + [5] * (count // 10) + [4] * (count - count//5 - count//3 - count//3 - count//10)
        
        # 부족한 경우 1급으로 채움
        while len(grades) < count:
            grades.append(1)
        
        for i in range(count):
            staff_data.append({
                "staff_id": 4000 + i + 1,
                "name": f"{names[i % len(names)]}{position}사{i+1}",
                "grade": grades[i],
                "total_hours": 209,
                "position": position
            })
        
        return staff_data
    
    def get_shift_config(self, shift_type: int) -> Tuple[List[str], Dict[str, int]]:
        """교대 유형별 시프트 구성을 반환합니다."""
        if shift_type == 3:
            return ["Day", "Evening", "Night", "Off"], {"Day": 8, "Evening": 8, "Night": 8, "Off": 0}
        elif shift_type == 4:
            return ["Early", "Day", "Evening", "Night", "Off"], {"Early": 8, "Day": 8, "Evening": 8, "Night": 8, "Off": 0}
        else:  # 5교대
            return ["Early", "Day", "Late", "Evening", "Night", "Off"], {"Early": 8, "Day": 8, "Late": 8, "Evening": 8, "Night": 8, "Off": 0}
    
    def send_request_with_timing(self, request_data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], float]:
        """서버에 요청을 보내고 응답 시간을 측정합니다."""
        start_time = time.time()
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(30)  # 30초 타임아웃
                sock.connect((self.host, self.port))
                
                json_data = json.dumps(request_data, ensure_ascii=False)
                json_bytes = json_data.encode('utf-8')
                
                total_size = len(json_bytes)
                header = struct.pack('<II', total_size, total_size)
                
                sock.send(header + json_bytes)
                
                response_header = sock.recv(8)
                if len(response_header) < 8:
                    return None, time.time() - start_time
                
                total_size, json_size = struct.unpack('<II', response_header)
                
                response_data = b""
                while len(response_data) < json_size:
                    chunk = sock.recv(json_size - len(response_data))
                    if not chunk:
                        break
                    response_data += chunk
                
                response_time = time.time() - start_time
                return json.loads(response_data.decode('utf-8')), response_time
                
        except Exception as e:
            response_time = time.time() - start_time
            print(f"❌ 요청 실패 ({response_time:.2f}초): {e}")
            return None, response_time
    
    def analyze_fairness(self, schedule_data: List[Dict]) -> Dict[str, Any]:
        """근무표 데이터에서 형평성을 분석합니다."""
        staff_off_days = defaultdict(int)
        staff_work_days = defaultdict(int)
        staff_names = {}
        total_days = 0
        
        # 날짜 수집
        dates = set()
        for entry in schedule_data:
            dates.add(entry['date'])
        total_days = len(dates)
        
        # 직원별 휴무일/근무일 계산
        for entry in schedule_data:
            shift = entry['shift']
            for person in entry['people']:
                staff_id = person['staff_id']
                staff_names[staff_id] = person['name']
                
                if shift == 'Off':
                    staff_off_days[staff_id] += 1
                else:
                    staff_work_days[staff_id] += 1
        
        # 형평성 지표 계산
        off_days_list = list(staff_off_days.values())
        if not off_days_list:
            return {"error": "No off days data found"}
        
        min_off = min(off_days_list)
        max_off = max(off_days_list)
        avg_off = statistics.mean(off_days_list)
        std_off = statistics.stdev(off_days_list) if len(off_days_list) > 1 else 0
        
        # 형평성 점수 (0-100, 높을수록 공정)
        fairness_score = max(0, 100 - ((max_off - min_off) * 20))  # 편차 1일당 20점 감점
        
        return {
            "total_days": total_days,
            "staff_count": len(staff_off_days),
            "min_off_days": min_off,
            "max_off_days": max_off,
            "avg_off_days": round(avg_off, 1),
            "std_off_days": round(std_off, 2),
            "range_off_days": max_off - min_off,
            "fairness_score": round(fairness_score, 1),
            "fairness_grade": self.get_fairness_grade(fairness_score),
            "staff_distribution": dict(staff_off_days)
        }
    
    def get_fairness_grade(self, score: float) -> str:
        """형평성 점수를 등급으로 변환합니다."""
        if score >= 90:
            return "S+ (완벽)"
        elif score >= 80:
            return "S (매우 양호)"
        elif score >= 70:
            return "A (양호)"
        elif score >= 60:
            return "B (보통)"
        elif score >= 50:
            return "C (개선 필요)"
        else:
            return "D (불량)"
    
    def run_single_test(self, staff_count: int, shift_type: int, month: int = 7) -> Dict[str, Any]:
        """단일 테스트를 실행합니다."""
        print(f"🧪 테스트: {staff_count}명 {shift_type}교대 시스템")
        
        staff_data = self.generate_staff_data(staff_count, "간호")
        shifts, shift_hours = self.get_shift_config(shift_type)
        
        request = {
            "protocol": "py_gen_timetable",
            "data": {
                "staff_data": {
                    "staff": staff_data
                },
                "position": "간호",
                "target_month": f"2025-{month:02d}",
                "custom_rules": {
                    "shifts": shifts,
                    "shift_hours": shift_hours,
                    "night_shifts": ["Night"],
                    "off_shifts": ["Off"]
                }
            }
        }
        
        response, response_time = self.send_request_with_timing(request)
        
        result = {
            "staff_count": staff_count,
            "shift_type": shift_type,
            "month": month,
            "response_time": round(response_time, 3),
            "success": False,
            "fairness_analysis": None,
            "constraint_violations": [],
            "performance_grade": "F"
        }
        
        if response and response.get("resp") == "success":
            result["success"] = True
            schedule_data = response.get("data", [])
            
            # 형평성 분석
            fairness = self.analyze_fairness(schedule_data)
            result["fairness_analysis"] = fairness
            
            # 제약조건 위반 검사
            violations = self.check_constraints(schedule_data, staff_data)
            result["constraint_violations"] = violations
            
            # 종합 성능 등급
            result["performance_grade"] = self.calculate_performance_grade(response_time, fairness, violations)
            
            print(f"   ✅ 성공 | 시간: {response_time:.3f}초 | 형평성: {fairness['fairness_grade']} | 성능: {result['performance_grade']}")
        else:
            print(f"   ❌ 실패 | 시간: {response_time:.3f}초")
            if response:
                result["error"] = response.get("resp", "Unknown error")
        
        return result
    
    def check_constraints(self, schedule_data: List[Dict], staff_data: List[Dict]) -> List[str]:
        """제약조건 위반사항을 검사합니다."""
        violations = []
        
        # 신규 간호사(grade 5) 야간 근무 검사
        newbie_ids = {staff["staff_id"] for staff in staff_data if staff.get("grade") == 5}
        
        for entry in schedule_data:
            if entry["shift"] == "Night":
                for person in entry["people"]:
                    if person["staff_id"] in newbie_ids:
                        violations.append(f"신규간호사 {person['name']} 야간근무 위반 ({entry['date']})")
        
        # TODO: 추가 제약조건 검사 (연속 야간 근무, 휴무 후 야간 등)
        
        return violations
    
    def calculate_performance_grade(self, response_time: float, fairness: Dict, violations: List) -> str:
        """종합 성능 등급을 계산합니다."""
        score = 100
        
        # 응답시간 점수 (1초 기준)
        if response_time > 2.0:
            score -= 30
        elif response_time > 1.0:
            score -= 15
        elif response_time > 0.5:
            score -= 5
        
        # 형평성 점수 반영
        fairness_score = fairness.get("fairness_score", 0)
        score = score * 0.4 + fairness_score * 0.5
        
        # 제약조건 위반 감점
        score -= len(violations) * 10
        
        # 등급 산출
        if score >= 90:
            return "S+"
        elif score >= 80:
            return "S"
        elif score >= 70:
            return "A"
        elif score >= 60:
            return "B"
        else:
            return "C"
    
    def run_comprehensive_tests(self):
        """종합 테스트를 실행합니다."""
        print("🚀 시프트 스케줄러 v5.0 종합 성능 테스트")
        print("=" * 70)
        print("📋 테스트 시나리오:")
        print("  • 직원 수: 10명, 15명, 20명, 25명, 30명")
        print("  • 교대 유형: 3교대, 4교대, 5교대") 
        print("  • 측정 항목: 처리시간, 형평성, 제약조건 준수")
        print("=" * 70)
        
        staff_counts = [10, 15, 20, 25, 30]
        shift_types = [3, 4, 5]
        
        start_time = time.time()
        test_number = 1
        total_tests = len(staff_counts) * len(shift_types)
        
        for staff_count in staff_counts:
            for shift_type in shift_types:
                print(f"\n[{test_number}/{total_tests}]", end=" ")
                result = self.run_single_test(staff_count, shift_type, 7)  # 7월 (31일)
                self.test_results.append(result)
                test_number += 1
                
                # 서버 부하 방지를 위해 잠시 대기
                time.sleep(0.5)
        
        total_time = time.time() - start_time
        
        # 결과 분석 및 출력
        self.analyze_and_report_results(total_time)
    
    def analyze_and_report_results(self, total_time: float):
        """테스트 결과를 분석하고 리포트를 생성합니다."""
        print(f"\n" + "=" * 70)
        print("📊 종합 테스트 결과 분석")
        print("=" * 70)
        print(f"⏱️ 전체 테스트 시간: {total_time:.1f}초")
        print(f"📋 총 테스트 수: {len(self.test_results)}개")
        
        # 성공률 계산
        successful_tests = [r for r in self.test_results if r["success"]]
        success_rate = len(successful_tests) / len(self.test_results) * 100
        print(f"✅ 성공률: {success_rate:.1f}% ({len(successful_tests)}/{len(self.test_results)})")
        
        if not successful_tests:
            print("❌ 성공한 테스트가 없습니다.")
            return
        
        # 성능 지표 분석
        response_times = [r["response_time"] for r in successful_tests]
        avg_time = statistics.mean(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        print(f"\n⏱️ 응답 시간 분석:")
        print(f"  • 평균: {avg_time:.3f}초")
        print(f"  • 최소: {min_time:.3f}초")  
        print(f"  • 최대: {max_time:.3f}초")
        
        # 형평성 지표 분석
        fairness_scores = [r["fairness_analysis"]["fairness_score"] for r in successful_tests if r.get("fairness_analysis")]
        if fairness_scores:
            avg_fairness = statistics.mean(fairness_scores)
            print(f"\n⚖️ 형평성 분석:")
            print(f"  • 평균 형평성 점수: {avg_fairness:.1f}/100")
            print(f"  • S급 이상: {len([s for s in fairness_scores if s >= 80])}개")
            print(f"  • A급 이상: {len([s for s in fairness_scores if s >= 70])}개")
        
        # 규모별 성능 분석
        print(f"\n📈 규모별 성능 분석:")
        for staff_count in [10, 15, 20, 25, 30]:
            staff_results = [r for r in successful_tests if r["staff_count"] == staff_count]
            if staff_results:
                avg_time = statistics.mean([r["response_time"] for r in staff_results])
                avg_fairness = statistics.mean([r["fairness_analysis"]["fairness_score"] for r in staff_results if r.get("fairness_analysis")])
                print(f"  • {staff_count}명: 평균 {avg_time:.3f}초, 형평성 {avg_fairness:.1f}점")
        
        # 교대별 성능 분석
        print(f"\n🔄 교대별 성능 분석:")
        for shift_type in [3, 4, 5]:
            shift_results = [r for r in successful_tests if r["shift_type"] == shift_type]
            if shift_results:
                avg_time = statistics.mean([r["response_time"] for r in shift_results])
                avg_fairness = statistics.mean([r["fairness_analysis"]["fairness_score"] for r in shift_results if r.get("fairness_analysis")])
                print(f"  • {shift_type}교대: 평균 {avg_time:.3f}초, 형평성 {avg_fairness:.1f}점")
        
        # 최고 성능 및 최저 성능
        best_result = max(successful_tests, key=lambda x: x.get("fairness_analysis", {}).get("fairness_score", 0))
        worst_result = min(successful_tests, key=lambda x: x.get("fairness_analysis", {}).get("fairness_score", 0))
        
        print(f"\n🏆 최고 성능:")
        print(f"  • {best_result['staff_count']}명 {best_result['shift_type']}교대: {best_result['response_time']:.3f}초, 형평성 {best_result.get('fairness_analysis', {}).get('fairness_score', 0):.1f}점")
        
        print(f"\n📉 최저 성능:")
        print(f"  • {worst_result['staff_count']}명 {worst_result['shift_type']}교대: {worst_result['response_time']:.3f}초, 형평성 {worst_result.get('fairness_analysis', {}).get('fairness_score', 0):.1f}점")
        
        # 상세 결과 테이블
        print(f"\n📋 상세 결과 테이블:")
        print("직원수 | 교대 | 시간(초) | 형평성 | 편차 | 등급")
        print("-" * 45)
        for result in successful_tests:
            fa = result.get("fairness_analysis", {})
            print(f"{result['staff_count']:4d}명 | {result['shift_type']}교대 | {result['response_time']:6.3f} | {fa.get('fairness_score', 0):5.1f} | {fa.get('range_off_days', 'N/A'):3} | {result['performance_grade']:2}")

if __name__ == "__main__":
    tester = ComprehensivePerformanceTest()
    tester.run_comprehensive_tests()