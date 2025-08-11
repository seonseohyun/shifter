#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerShell 버퍼링 문제 해결을 위한 shift_server_optimized.py 개선 버전
변경이 필요한부분.txt에 기술된 엔터 입력 문제를 해결합니다.
"""

import os
import sys
import logging
import socket
import struct
import json
import threading
from datetime import datetime, timedelta
from ortools.sat.python import cp_model
import openai

# =============================================================================
# 1. PowerShell 버퍼링 문제 해결을 위한 초기 설정
# =============================================================================

# 환경 변수 설정 (이미 설정되어 있지만 확실히 하기 위해)
os.environ["PYTHONUNBUFFERED"] = "1"

# stdout/stderr을 line-buffered로 강제 재바인딩
try:
    sys.stdout = open(sys.stdout.fileno(), mode='w', buffering=1, encoding='utf-8', errors='replace')
    sys.stderr = open(sys.stderr.fileno(), mode='w', buffering=1, encoding='utf-8', errors='replace')
    print("✅ stdout/stderr line-buffered 모드 설정 완료")
except Exception as e:
    print(f"⚠️ stdout/stderr 재설정 실패: {e}")

# logging을 stdout으로 강제 전환하여 PowerShell 버퍼링 문제 해결
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],  # stderr 대신 stdout 사용
    force=True
)

logger = logging.getLogger(__name__)

# 초기화 확인 로그
logger.info("🚀 PowerShell 버퍼링 문제 해결 버전 시작")
logger.info("📤 모든 로그가 stdout으로 line-buffered 모드로 출력됩니다")

# =============================================================================
# 2. OpenAI 설정
# =============================================================================

# OpenAI API 키 설정
openai.api_key = os.getenv('OPENAI_API_KEY')

if not openai.api_key:
    logger.warning("⚠️ OPENAI_API_KEY 환경변수가 설정되지 않음")
    logger.warning("⚠️ 인수인계 명료화 기능이 비활성화됩니다")

# =============================================================================
# 3. 근무표 생성 클래스 (기존 로직 유지, 로깅만 개선)
# =============================================================================

class ShiftScheduler:
    def __init__(self):
        self.staff_count = 0
        self.shift_count = 0
        self.days_in_month = 0
        self.staff_names = []
        self.shift_names = []
        
        logger.info("📋 ShiftScheduler 초기화 완료")
    
    def generate_schedule(self, staff_names, shift_names, days_in_month):
        """근무표 생성 메인 함수"""
        logger.info(f"📊 근무표 생성 시작: {len(staff_names)}명, {len(shift_names)}교대, {days_in_month}일")
        
        self.staff_names = staff_names
        self.shift_names = shift_names
        self.staff_count = len(staff_names)
        self.shift_count = len(shift_names)
        self.days_in_month = days_in_month
        
        # 제약조건 검증
        if not self._validate_constraints():
            logger.error("❌ 제약조건 검증 실패")
            return None
        
        # OR-Tools 모델 생성
        model = cp_model.CpModel()
        solver = cp_model.CpSolver()
        
        # 변수 생성
        shifts = {}
        for s in range(self.staff_count):
            for d in range(self.days_in_month):
                for t in range(self.shift_count):
                    shifts[(s, d, t)] = model.NewBoolVar(f'shift_s{s}_d{d}_t{t}')
        
        logger.info("🔧 CP-SAT 모델 변수 생성 완료")
        
        # 제약조건 추가
        self._add_constraints(model, shifts)
        logger.info("📐 모든 제약조건 추가 완료")
        
        # 목적함수 설정 (형평성 최대화)
        self._add_fairness_objective(model, shifts)
        logger.info("🎯 형평성 목적함수 설정 완료")
        
        # 해결
        logger.info("🔍 제약 만족 문제 해결 시작...")
        status = solver.Solve(model)
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            logger.info("✅ 근무표 생성 성공!")
            schedule = self._extract_solution(solver, shifts)
            fairness_stats = self._calculate_fairness_stats(schedule)
            
            logger.info(f"📈 형평성 통계: 최대편차 {fairness_stats['max_deviation']}, "
                       f"평균편차 {fairness_stats['avg_deviation']:.2f}")
            
            return {
                'schedule': schedule,
                'fairness_stats': fairness_stats,
                'solver_status': 'OPTIMAL' if status == cp_model.OPTIMAL else 'FEASIBLE'
            }
        else:
            logger.error(f"❌ 해결 실패: {solver.StatusName(status)}")
            return None
    
    def _validate_constraints(self):
        """기본 제약조건 검증"""
        if self.staff_count < 3:
            logger.error(f"❌ 직원 수 부족: {self.staff_count} < 3")
            return False
        
        if self.shift_count < 2:
            logger.error(f"❌ 교대 수 부족: {self.shift_count} < 2")
            return False
        
        # 수학적 적합성 검증
        min_required_staff = self.shift_count * self.days_in_month
        max_available_shifts = self.staff_count * self.days_in_month
        
        if min_required_staff > max_available_shifts:
            logger.error(f"❌ 수학적 불가능: 필요 {min_required_staff} > 가능 {max_available_shifts}")
            return False
        
        # 부적합한 조합 경고
        if self.staff_count <= 10 and self.shift_count >= 4:
            logger.warning(f"⚠️ 부적합한 조합: {self.staff_count}명 {self.shift_count}교대")
            logger.warning("⚠️ 10명 이하에서는 3교대 권장")
        
        return True
    
    def _add_constraints(self, model, shifts):
        """모든 제약조건 추가"""
        # 1. 매일 모든 시간대에 1명씩 배치
        for d in range(self.days_in_month):
            for t in range(self.shift_count):
                model.Add(sum(shifts[(s, d, t)] for s in range(self.staff_count)) == 1)
        
        # 2. 각 직원은 하루에 최대 1개 시간대만
        for s in range(self.staff_count):
            for d in range(self.days_in_month):
                model.Add(sum(shifts[(s, d, t)] for t in range(self.shift_count)) <= 1)
        
        # 3. 연속 근무 제한 (최대 3일)
        for s in range(self.staff_count):
            for d in range(self.days_in_month - 3):
                working_days = []
                for day in range(d, d + 4):
                    day_work = model.NewBoolVar(f'working_s{s}_d{day}')
                    model.Add(day_work == sum(shifts[(s, day, t)] for t in range(self.shift_count)))
                    working_days.append(day_work)
                model.Add(sum(working_days) <= 3)
        
        # 4. 동적 형평성 제약조건 (직원 수 기반)
        self._add_dynamic_fairness_constraints(model, shifts)
    
    def _add_dynamic_fairness_constraints(self, model, shifts):
        """직원 수에 따른 동적 형평성 제약조건"""
        total_shifts = self.days_in_month * self.shift_count
        avg_shifts = total_shifts // self.staff_count
        
        # 직원 수에 따른 허용 편차 계산
        if self.staff_count <= 10:
            max_deviation = 2
        elif self.staff_count <= 20:
            max_deviation = 3
        else:
            max_deviation = 4
        
        logger.info(f"📊 형평성 제약: 평균 {avg_shifts}회, 최대편차 ±{max_deviation}")
        
        # 각 직원의 총 근무일 수 제한
        for s in range(self.staff_count):
            total_shifts_var = sum(shifts[(s, d, t)] 
                                  for d in range(self.days_in_month) 
                                  for t in range(self.shift_count))
            
            model.Add(total_shifts_var >= avg_shifts - max_deviation)
            model.Add(total_shifts_var <= avg_shifts + max_deviation)
    
    def _add_fairness_objective(self, model, shifts):
        """형평성 최대화 목적함수"""
        total_shifts = self.days_in_month * self.shift_count
        avg_shifts = total_shifts // self.staff_count
        
        # 편차의 제곱합 최소화
        deviations = []
        for s in range(self.staff_count):
            staff_total = sum(shifts[(s, d, t)] 
                             for d in range(self.days_in_month) 
                             for t in range(self.shift_count))
            
            # 편차 계산을 위한 보조 변수
            deviation_var = model.NewIntVar(-10, 10, f'deviation_s{s}')
            model.Add(deviation_var == staff_total - avg_shifts)
            
            # 절댓값을 위한 변수
            abs_deviation = model.NewIntVar(0, 10, f'abs_deviation_s{s}')
            model.AddAbsEquality(abs_deviation, deviation_var)
            deviations.append(abs_deviation)
        
        # 총 편차 최소화
        model.Minimize(sum(deviations))
    
    def _extract_solution(self, solver, shifts):
        """해결된 근무표 추출"""
        schedule = {}
        
        for d in range(self.days_in_month):
            day_key = f"day_{d+1}"
            schedule[day_key] = {}
            
            for t in range(self.shift_count):
                shift_key = self.shift_names[t]
                
                # 해당 시간대에 배정된 직원 찾기
                assigned_staff = None
                for s in range(self.staff_count):
                    if solver.Value(shifts[(s, d, t)]) == 1:
                        assigned_staff = self.staff_names[s]
                        break
                
                schedule[day_key][shift_key] = assigned_staff or "미배정"
        
        return schedule
    
    def _calculate_fairness_stats(self, schedule):
        """형평성 통계 계산"""
        staff_work_count = {name: 0 for name in self.staff_names}
        
        # 각 직원의 총 근무일 수 계산
        for day_schedule in schedule.values():
            for assigned_staff in day_schedule.values():
                if assigned_staff in staff_work_count:
                    staff_work_count[assigned_staff] += 1
        
        work_counts = list(staff_work_count.values())
        avg_work = sum(work_counts) / len(work_counts)
        max_deviation = max(work_counts) - min(work_counts)
        avg_deviation = sum(abs(count - avg_work) for count in work_counts) / len(work_counts)
        
        return {
            'staff_work_count': staff_work_count,
            'avg_work': avg_work,
            'max_deviation': max_deviation,
            'avg_deviation': avg_deviation
        }

# =============================================================================
# 4. 인수인계 명료화 기능 (기존 로직 유지)
# =============================================================================

def enhance_handover_text(text):
    """OpenAI를 사용한 인수인계 문장 명료화"""
    if not openai.api_key:
        logger.warning("⚠️ OpenAI API 키가 없어 원본 텍스트 반환")
        return text
    
    try:
        logger.info("🤖 OpenAI GPT-4 인수인계 명료화 요청 시작")
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": "당신은 병원 간호사들의 인수인계 문장을 명료하고 체계적으로 개선하는 전문가입니다. 의료진이 빠르게 이해할 수 있도록 간결하면서도 정확한 표현으로 다시 작성해주세요."
                },
                {
                    "role": "user", 
                    "content": f"다음 인수인계 내용을 더 명료하고 체계적으로 개선해주세요:\n\n{text}"
                }
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        enhanced_text = response.choices[0].message.content.strip()
        logger.info("✅ OpenAI 인수인계 명료화 완료")
        
        return enhanced_text
        
    except Exception as e:
        logger.error(f"❌ OpenAI 인수인계 명료화 실패: {e}")
        return text

# =============================================================================
# 5. TCP 서버 클래스 (버퍼링 문제 해결 포함)
# =============================================================================

class ShiftSchedulerServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.scheduler = ShiftScheduler()
        self.running = False
        
        logger.info(f"🌐 TCP 서버 초기화: {host}:{port}")
    
    def start(self):
        """서버 시작"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            
            self.running = True
            logger.info(f"🚀 서버 시작됨: {self.host}:{self.port}")
            logger.info("📞 클라이언트 연결 대기 중...")
            
            while self.running:
                try:
                    conn, addr = server_socket.accept()
                    logger.info(f"🔗 클라이언트 연결: {addr}")
                    
                    # 각 클라이언트를 별도 스레드에서 처리
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(conn, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    logger.error(f"❌ 클라이언트 수락 오류: {e}")
    
    def handle_client(self, conn, addr):
        """클라이언트 요청 처리 (버퍼링 문제 해결 포함)"""
        try:
            conn.settimeout(10.0)  # 타임아웃 설정
            
            # 바이너리 헤더 읽기 (8바이트: totalSize + jsonSize)
            header_data = conn.recv(8)
            if len(header_data) != 8:
                logger.error(f"❌ 헤더 길이 오류: {len(header_data)}/8")
                return
            
            # 리틀엔디안으로 헤더 파싱
            total_size, json_size = struct.unpack('<II', header_data)
            logger.info(f"📦 바이너리 헤더: totalSize={total_size}, jsonSize={json_size}")
            
            # JSON 데이터 읽기
            json_data = conn.recv(json_size).decode('utf-8')
            request = json.loads(json_data)
            
            logger.info(f"📨 요청 수신: {request.get('protocol', 'unknown')}")
            
            # 프로토콜별 처리
            if request.get('protocol') in ['py_gen_timetable', 'py_gen_schedule']:
                response = self.handle_schedule_request(request)
            elif request.get('protocol') == 'py_handover_summary':
                response = self.handle_handover_request(request)
            else:
                logger.warning(f"⚠️ 알 수 없는 프로토콜: {request.get('protocol')}")
                response = {
                    'protocol': request.get('protocol', 'unknown'),
                    'resp': 'error',
                    'data': {'error': 'Unknown protocol'}
                }
            
            # 응답 전송
            self.send_response(conn, response)
            logger.info("✅ 응답 전송 완료")
            
        except socket.timeout:
            logger.error(f"⏰ {addr} 타임아웃")
        except Exception as e:
            logger.error(f"❌ {addr} 처리 오류: {e}")
        finally:
            conn.close()
            logger.info(f"🔌 {addr} 연결 종료")
    
    def handle_schedule_request(self, request):
        """근무표 생성 요청 처리"""
        try:
            data = request.get('data', {})
            staff_names = data.get('staff_names', [])
            shift_names = data.get('shift_names', [])
            days_in_month = data.get('days_in_month', 30)
            
            logger.info(f"📋 근무표 생성 요청 처리 시작")
            
            # 근무표 생성
            result = self.scheduler.generate_schedule(staff_names, shift_names, days_in_month)
            
            if result:
                logger.info("✅ 근무표 생성 성공")
                return {
                    'protocol': request.get('protocol'),
                    'resp': 'success',
                    'data': {
                        'schedule': result['schedule'],
                        'fairness_stats': result['fairness_stats'],
                        'solver_status': result['solver_status']
                    }
                }
            else:
                logger.error("❌ 근무표 생성 실패")
                return {
                    'protocol': request.get('protocol'),
                    'resp': 'error',
                    'data': {'error': 'Schedule generation failed'}
                }
                
        except Exception as e:
            logger.error(f"❌ 근무표 요청 처리 오류: {e}")
            return {
                'protocol': request.get('protocol'),
                'resp': 'error',
                'data': {'error': str(e)}
            }
    
    def handle_handover_request(self, request):
        """인수인계 명료화 요청 처리"""
        try:
            data = request.get('data', {})
            original_text = data.get('text', '')
            
            logger.info("📝 인수인계 명료화 요청 처리 시작")
            
            enhanced_text = enhance_handover_text(original_text)
            
            logger.info("✅ 인수인계 명료화 완료")
            return {
                'protocol': 'py_handover_summary',
                'resp': 'success', 
                'data': {
                    'original_text': original_text,
                    'enhanced_text': enhanced_text
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 인수인계 요청 처리 오류: {e}")
            return {
                'protocol': 'py_handover_summary',
                'resp': 'error',
                'data': {'error': str(e)}
            }
    
    def send_response(self, conn, response):
        """응답 전송 (리틀엔디안 바이너리 프로토콜)"""
        try:
            # JSON 직렬화
            response_json = json.dumps(response, ensure_ascii=False)
            response_bytes = response_json.encode('utf-8')
            
            json_size = len(response_bytes)
            total_size = 8 + json_size  # 헤더 8바이트 + JSON 크기
            
            # 리틀엔디안 바이너리 헤더 생성
            header = struct.pack('<II', total_size, json_size)
            
            # 헤더 + JSON 데이터 전송
            conn.sendall(header + response_bytes)
            
            logger.info(f"📤 응답 전송: {total_size}바이트 (JSON: {json_size}바이트)")
            
        except Exception as e:
            logger.error(f"❌ 응답 전송 오류: {e}")
    
    def stop(self):
        """서버 중지"""
        self.running = False
        logger.info("🛑 서버 중지 요청됨")

# =============================================================================
# 6. 메인 실행부
# =============================================================================

def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("🚀 Shift Scheduler Server with PowerShell Fix v5.1")
    logger.info("=" * 60)
    logger.info("📋 기능: 근무표 생성 + OpenAI 인수인계 명료화")
    logger.info("🔧 개선: PowerShell 버퍼링 문제 해결")
    logger.info("📤 출력: 모든 로그 stdout 라인 버퍼링")
    logger.info("=" * 60)
    
    # 환경 검증
    if openai.api_key:
        logger.info("✅ OpenAI API 키 확인됨 - 인수인계 명료화 활성화")
    else:
        logger.warning("⚠️ OpenAI API 키 없음 - 인수인계 명료화 비활성화")
    
    # 서버 시작
    server = ShiftSchedulerServer()
    
    try:
        logger.info("🌐 TCP 서버 시작 중...")
        server.start()
    except KeyboardInterrupt:
        logger.info("⌨️ 키보드 인터럽트 감지")
    except Exception as e:
        logger.error(f"❌ 서버 오류: {e}")
    finally:
        server.stop()
        logger.info("👋 서버 종료됨")

if __name__ == "__main__":
    main()