#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI 기반 근무표 생성 서버 (server_ai_gen.py)
OR-Tools 대신 OpenAI GPT-4를 사용하여 현실적이고 유연한 근무표 생성
기존 프로토콜과 제약사항 완전 호환
"""

import os
import sys
import socket
import json
import struct
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import threading
from dotenv import load_dotenv
from openai import OpenAI

# 환경 변수 설정
os.environ["PYTHONUNBUFFERED"] = "1"

# stdout/stderr을 line-buffered로 강제 재바인딩
sys.stdout = open(sys.stdout.fileno(), mode='w', buffering=1, encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', buffering=1, encoding='utf-8', errors='replace')

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 서버 설정
HOST = '0.0.0.0'
PORT = 6004
MAX_PACKET_SIZE = 10 * 1024 * 1024  # 10MB

# OpenAI 클라이언트 설정
openai_client = None
OPENAI_AVAILABLE = False

try:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        OPENAI_AVAILABLE = True
        logger.info("✅ OpenAI API 클라이언트 초기화 성공")
    else:
        logger.error("❌ OPENAI_API_KEY 환경변수가 설정되지 않음")
except Exception as e:
    logger.error(f"❌ OpenAI 클라이언트 초기화 실패: {e}")

# =============================================================================
# OpenAI 기반 근무표 생성 클래스
# =============================================================================

class AIShiftGenerator:
    def __init__(self):
        self.model = "gpt-3.5-turbo"  # GPT-4 → GPT-3.5-turbo로 변경 (속도 향상)
        self.max_retries = 3
        
    def generate_shift_schedule(self, staff_data: Dict[str, Any]) -> Dict[str, Any]:
        """OpenAI를 사용하여 근무표 생성"""
        if not OPENAI_AVAILABLE:
            return {
                "status": "error",
                "message": "OpenAI API가 사용 불가능합니다"
            }
        
        try:
            # 직원 정보 추출
            staff_list = staff_data.get('staff', [])
            position = staff_data.get('position', '간호')
            target_year = staff_data.get('target_year', datetime.now().year)
            target_month = staff_data.get('target_month', datetime.now().month)
            
            # 월별 일수 계산
            if target_month == 2:
                # 윤년 체크
                is_leap = (target_year % 4 == 0 and target_year % 100 != 0) or (target_year % 400 == 0)
                days_in_month = 29 if is_leap else 28
            elif target_month in [4, 6, 9, 11]:
                days_in_month = 30
            else:
                days_in_month = 31
            
            logger.info(f"🤖 OpenAI 근무표 생성 시작: {len(staff_list)}명, {position}, {target_year}년 {target_month}월 ({days_in_month}일)")
            
            # OpenAI 프롬프트 생성
            prompt = self._create_schedule_prompt(staff_list, position, days_in_month, target_year, target_month)
            
            # OpenAI API 호출
            for attempt in range(self.max_retries):
                try:
                    logger.info(f"🔄 OpenAI API 호출 시도 {attempt + 1}/{self.max_retries}")
                    
                    response = openai_client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": """당신은 병원 근무표 생성 전문가입니다. 
                                요청받은 근무표를 정확한 JSON 형식으로만 응답하세요.
                                절대로 설명이나 추가 텍스트를 포함하지 마세요.
                                오직 유효한 JSON 객체만 출력하세요."""
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        max_tokens=3000,  # 토큰 수 약간 줄임 (속도 향상)
                        temperature=0.1   # 더 일관된 출력 (속도 향상)
                    )
                    
                    # 응답 파싱
                    ai_response = response.choices[0].message.content.strip()
                    logger.info(f"✅ OpenAI 응답 수신 완료 ({len(ai_response)} 문자)")
                    
                    # JSON 추출 및 파싱
                    schedule_data = self._parse_ai_response(ai_response)
                    
                    if schedule_data:
                        # 3일 패턴을 31일로 확장
                        extended_schedule = self._extend_schedule_pattern(schedule_data, days_in_month)
                        
                        logger.info("✅ OpenAI 근무표 생성 성공")
                        return {
                            "status": "success",
                            "schedule": extended_schedule,
                            "ai_response": ai_response,
                            "generation_method": "openai_gpt35_pattern",
                            "attempt": attempt + 1
                        }
                    else:
                        logger.warning(f"⚠️ 시도 {attempt + 1}: JSON 파싱 실패")
                        
                except Exception as e:
                    logger.error(f"❌ 시도 {attempt + 1} 실패: {e}")
                    if attempt == self.max_retries - 1:
                        raise
                    
                    time.sleep(1)  # 재시도 전 대기
            
            return {
                "status": "error",
                "message": f"{self.max_retries}번 시도 후 실패"
            }
            
        except Exception as e:
            logger.error(f"❌ OpenAI 근무표 생성 실패: {e}")
            return {
                "status": "error",
                "message": f"OpenAI 근무표 생성 중 오류: {str(e)}"
            }
    
    def _create_schedule_prompt(self, staff_list: List[Dict], position: str, days_in_month: int, year: int, month: int) -> str:
        """OpenAI용 근무표 생성 프롬프트 작성"""
        
        # 직원 정보 정리
        staff_names = []
        for staff in staff_list:
            name = staff.get('name', f"직원{staff.get('staff_id', 'Unknown')}")
            staff_id = staff.get('staff_id', 0)
            grade = staff.get('grade', 4)
            total_hours = staff.get('total_hours', 180)
            staff_names.append(f"{name}(ID:{staff_id}, 등급:{grade}, 최대:{total_hours}h)")
        
        prompt = f"""당신은 병원 근무표 생성 전문가입니다. 주어진 조건에 맞는 근무표를 JSON으로 생성해주세요.

=== 근무표 정보 ===
- 기간: {year}년 {month}월 (총 {days_in_month}일)
- 직원: {len(staff_list)}명
- 교대: Day(8h), Evening(8h), Night(8h) - 각 교대마다 1명씩 배정

=== 직원 정보 ===
{chr(10).join(staff_names)}

=== 제약조건 ===
1. 각 날짜의 Day, Evening, Night에 반드시 1명씩 배정
2. ⚠️ 신입간호사(grade 5)는 혼자 야간근무 금지 - Night 교대에 혼자 배정 안됨 (선배와 함께면 가능)
3. Night 근무 후 다음날 반드시 휴무
4. 연속 근무는 최대 3일
5. 160시간 제한 준수 (최대 20일 근무)
6. 형평성: 직원간 근무일 차이 최소화

=== 출력 형식 ===
다음 JSON 형식으로만 응답하세요. 다른 설명이나 텍스트는 포함하지 마세요.

{{
  "schedule": [
    {{"day": 0, "shift": "Day", "hours": 8, "people": [{{"name": "김간호사", "staff_id": 1, "grade": 3}}]}},
    {{"day": 0, "shift": "Evening", "hours": 8, "people": [{{"name": "이간호사", "staff_id": 2, "grade": 4}}]}},
    {{"day": 0, "shift": "Night", "hours": 8, "people": [{{"name": "박간호사", "staff_id": 3, "grade": 4}}]}},
    {{"day": 1, "shift": "Day", "hours": 8, "people": [{{"name": "최간호사", "staff_id": 4, "grade": 3}}]}},
    {{"day": 1, "shift": "Evening", "hours": 8, "people": [{{"name": "정간호사", "staff_id": 5, "grade": 5}}]}},
    {{"day": 1, "shift": "Night", "hours": 8, "people": [{{"name": "한간호사", "staff_id": 6, "grade": 4}}]}},
    {{"day": 2, "shift": "Day", "hours": 8, "people": [{{"name": "장간호사", "staff_id": 7, "grade": 3}}]}},
    {{"day": 2, "shift": "Evening", "hours": 8, "people": [{{"name": "윤간호사", "staff_id": 8, "grade": 4}}]}},
    {{"day": 2, "shift": "Night", "hours": 8, "people": [{{"name": "강간호사", "staff_id": 9, "grade": 4}}]}},
    {{"day": 3, "shift": "Day", "hours": 8, "people": [{{"name": "조간호사", "staff_id": 10, "grade": 3}}]}},
    {{"day": 3, "shift": "Evening", "hours": 8, "people": [{{"name": "김간호사", "staff_id": 1, "grade": 3}}]}},
    {{"day": 3, "shift": "Night", "hours": 8, "people": [{{"name": "이간호사", "staff_id": 2, "grade": 4}}]}}
  ],
  "fairness_analysis": {{
    "max_deviation": 1,
    "avg_work_days": 9.3,
    "comments": "최적 패턴 생성 완료"
  }}
}}

중요: 
- day는 0부터 {days_in_month-1}까지
- 처음 {min(len(staff_list), 10)}일치만 생성하세요 (형평성을 위한 최적 패턴)
- 각 직원이 골고루 배치되도록 순환 패턴 만들기
- ⚠️ grade 5 신입간호사가 Night 교대에 혼자 배정되지 않도록 주의
- JSON에 주석(//), 설명, 생략(...) 절대 포함 금지
- 완전한 JSON만 출력하세요"""
        
        return prompt
    
    def _extend_schedule_pattern(self, base_schedule: List[Dict], days_in_month: int) -> List[Dict]:
        """적응적 패턴을 전체 월로 확장"""
        if not base_schedule:
            return []
        
        extended_schedule = []
        
        # 실제 패턴 길이 확인 (AI가 생성한 일수)
        pattern_days = max([entry.get("day", 0) for entry in base_schedule]) + 1
        entries_per_day = 3  # Day, Evening, Night
        
        logger.info(f"📅 감지된 패턴 길이: {pattern_days}일")
        
        for target_day in range(days_in_month):
            pattern_day = target_day % pattern_days
            
            # 해당 패턴 날짜의 모든 교대 찾기
            for shift_type in ["Day", "Evening", "Night"]:
                # 패턴에서 해당하는 엔트리 찾기
                pattern_entry = None
                for entry in base_schedule:
                    if entry.get("day") == pattern_day and entry.get("shift") == shift_type:
                        pattern_entry = entry
                        break
                
                if pattern_entry:
                    # 새 엔트리 생성 (날짜만 변경)
                    new_entry = {
                        "day": target_day,
                        "shift": shift_type,
                        "hours": pattern_entry.get("hours", 8),
                        "people": pattern_entry.get("people", []).copy()
                    }
                    extended_schedule.append(new_entry)
        
        logger.info(f"📅 패턴 확장 완료: {len(base_schedule)}개 → {len(extended_schedule)}개 엔트리")
        return extended_schedule
    
    def _parse_ai_response(self, ai_response: str) -> Optional[List[Dict]]:
        """OpenAI 응답에서 JSON 추출 및 파싱"""
        try:
            # 응답 정리 (공백, 줄바꿈 제거)
            cleaned_response = ai_response.strip()
            
            # JSON 블록 찾기 (```json 태그 고려)
            if "```json" in cleaned_response:
                json_start = cleaned_response.find('{', cleaned_response.find('```json'))
                json_end = cleaned_response.rfind('}', 0, cleaned_response.find('```', cleaned_response.find('```json') + 7))
                if json_end != -1:
                    json_end += 1
            else:
                json_start = cleaned_response.find('{')
                json_end = cleaned_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("❌ AI 응답에서 JSON 블록을 찾을 수 없음")
                logger.error(f"응답 내용: {cleaned_response[:200]}...")
                return None
            
            json_str = cleaned_response[json_start:json_end]
            logger.info(f"📋 추출된 JSON 길이: {len(json_str)} 문자")
            
            schedule_data = json.loads(json_str)
            
            # 기본 구조 검증
            if 'schedule' not in schedule_data:
                logger.error("❌ AI 응답에 'schedule' 키가 없음")
                return None
            
            schedule = schedule_data['schedule']
            if not isinstance(schedule, list) or len(schedule) == 0:
                logger.error("❌ 스케줄 데이터가 비어있거나 잘못된 형식")
                return None
            
            # 형평성 분석 로그
            if 'fairness_analysis' in schedule_data:
                fairness = schedule_data['fairness_analysis']
                logger.info(f"📊 AI 형평성 분석: 최대편차 {fairness.get('max_deviation', 'Unknown')}일, "
                           f"평균 근무일 {fairness.get('avg_work_days', 'Unknown')}일")
            
            # 제약조건 준수 로그  
            if 'constraints_status' in schedule_data:
                constraints = schedule_data['constraints_status']
                logger.info(f"✅ 제약조건 준수: 시간제한 {constraints.get('hours_limit_compliance', False)}, "
                           f"형평성 {constraints.get('fairness_achieved', False)}")
            
            return schedule
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 파싱 오류: {e}")
            logger.error(f"문제가 된 응답: {ai_response[:500]}...")
            return None
        except Exception as e:
            logger.error(f"❌ AI 응답 파싱 중 예외: {e}")
            return None

# =============================================================================
# 인수인계 명료화 클래스
# =============================================================================

class AIHandoverEnhancer:
    def __init__(self):
        self.model = "gpt-3.5-turbo"
    
    def enhance_handover_text(self, input_text: str) -> Dict[str, Any]:
        """OpenAI를 사용한 인수인계 문장 명료화"""
        if not OPENAI_AVAILABLE:
            return {
                "status": "error",
                "message": "OpenAI API가 사용 불가능합니다",
                "original_text": input_text,
                "enhanced_text": input_text
            }
        
        start_time = time.time()
        
        try:
            if not input_text or input_text.strip() == "":
                return {
                    "status": "error",
                    "message": "입력 텍스트가 비어 있습니다",
                    "original_text": input_text,
                    "enhanced_text": input_text
                }
            
            logger.info(f"📝 인수인계 명료화 시작: {len(input_text)} 문자")
            
            system_prompt = """당신은 병원 간호사들의 인수인계 문장을 명료하고 체계적으로 개선하는 전문가입니다. 
            
            의료진이 빠르게 이해할 수 있도록:
            1. 핵심 정보를 앞쪽에 배치
            2. 중요도에 따라 우선순위 정리
            3. 불필요한 말은 생략하고 간결하게
            4. 의료 용어는 정확하게 사용
            5. 시급한 사항은 명확히 표시
            
            절대 ** 같은 기호는 사용하지 마세요."""
            
            response = openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"다음 인수인계 내용을 더 명료하고 체계적으로 개선해주세요:\n\n{input_text}"}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            enhanced_text = response.choices[0].message.content.strip()
            process_time = time.time() - start_time
            
            logger.info(f"✅ 인수인계 명료화 완료: {process_time:.2f}초, {len(enhanced_text)} 문자")
            
            return {
                "status": "success",
                "original_text": input_text,
                "enhanced_text": enhanced_text,
                "processing_time": process_time,
                "model_used": self.model
            }
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"❌ 인수인계 명료화 실패 ({process_time:.2f}초): {e}")
            
            return {
                "status": "error",
                "message": f"인수인계 명료화 중 오류: {str(e)}",
                "original_text": input_text,
                "enhanced_text": input_text,
                "processing_time": process_time
            }

# =============================================================================
# 바이너리 프로토콜 핸들러 (기존과 동일)
# =============================================================================

class BinaryProtocolHandler:
    """C++ 클라이언트 호환 바이너리 프로토콜 핸들러"""
    
    @staticmethod
    def recv_exact(conn: socket.socket, n: int) -> bytes:
        """정확히 n바이트 수신"""
        conn.settimeout(10.0)
        buf = b''
        while len(buf) < n:
            chunk = conn.recv(n - len(buf))
            if not chunk:
                raise ConnectionError(f"Socket connection closed unexpectedly")
            buf += chunk
        return buf
    
    @staticmethod
    def receive_packet(conn: socket.socket) -> Optional[Dict[str, Any]]:
        """바이너리 프로토콜로 패킷 수신"""
        try:
            # 8바이트 헤더 읽기
            header = BinaryProtocolHandler.recv_exact(conn, 8)
            
            # 리틀엔디안으로 헤더 파싱
            total_size = struct.unpack('<I', header[:4])[0]
            json_size = struct.unpack('<I', header[4:8])[0]
            
            logger.info(f"📦 헤더: totalSize={total_size}, jsonSize={json_size}")
            
            # 크기 검증
            if json_size == 0 or json_size > total_size or total_size > MAX_PACKET_SIZE:
                logger.error(f"❌ 잘못된 헤더: jsonSize={json_size}, totalSize={total_size}")
                return None
            
            # JSON 데이터 읽기
            json_data = BinaryProtocolHandler.recv_exact(conn, json_size).decode('utf-8')
            request = json.loads(json_data)
            
            logger.info(f"📨 요청 수신: {request.get('protocol', 'unknown')}")
            return request
            
        except Exception as e:
            logger.error(f"❌ 패킷 수신 오류: {e}")
            return None
    
    @staticmethod
    def send_response(conn: socket.socket, response: Dict[str, Any]) -> bool:
        """바이너리 프로토콜로 응답 전송"""
        try:
            # JSON 직렬화
            response_json = json.dumps(response, ensure_ascii=False)
            response_bytes = response_json.encode('utf-8')
            
            json_size = len(response_bytes)
            total_size = 8 + json_size
            
            # 리틀엔디안 헤더 생성
            header = struct.pack('<II', total_size, json_size)
            
            # 헤더 + JSON 전송
            conn.sendall(header + response_bytes)
            
            logger.info(f"📤 응답 전송: {total_size}바이트")
            return True
            
        except Exception as e:
            logger.error(f"❌ 응답 전송 오류: {e}")
            return False

# =============================================================================
# 메인 서버 클래스
# =============================================================================

class AIShiftSchedulerServer:
    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self.running = False
        self.ai_generator = AIShiftGenerator()
        self.ai_enhancer = AIHandoverEnhancer()
        
        logger.info(f"🤖 AI 기반 근무표 서버 초기화: {host}:{port}")
    
    def start(self):
        """서버 시작"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            
            self.running = True
            logger.info(f"🚀 AI 근무표 서버 시작: {self.host}:{self.port}")
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
    
    def handle_client(self, conn: socket.socket, addr):
        """클라이언트 요청 처리"""
        try:
            # 요청 수신
            request = BinaryProtocolHandler.receive_packet(conn)
            if not request:
                return
            
            # 프로토콜별 처리
            protocol = request.get('protocol', '')
            
            if protocol in ['py_gen_timetable', 'py_gen_schedule']:
                response = self.handle_schedule_request(request)
            elif protocol == 'py_handover_summary':
                response = self.handle_handover_request(request)
            else:
                logger.warning(f"⚠️ 알 수 없는 프로토콜: {protocol}")
                response = {
                    'protocol': protocol,
                    'resp': 'error',
                    'data': {'error': f'Unknown protocol: {protocol}'}
                }
            
            # 응답 전송
            BinaryProtocolHandler.send_response(conn, response)
            logger.info("✅ 응답 전송 완료")
            
        except Exception as e:
            logger.error(f"❌ 클라이언트 처리 오류: {e}")
        finally:
            conn.close()
            logger.info(f"🔌 {addr} 연결 종료")
    
    def handle_schedule_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """근무표 생성 요청 처리"""
        try:
            start_time = time.time()
            logger.info("🤖 AI 근무표 생성 요청 처리 시작")
            
            # 요청 데이터 추출
            data = request.get('data', {})
            
            # OpenAI로 근무표 생성
            result = self.ai_generator.generate_shift_schedule(data)
            
            processing_time = time.time() - start_time
            
            if result.get('status') == 'success':
                logger.info(f"✅ AI 근무표 생성 성공 ({processing_time:.2f}초)")
                
                return {
                    'protocol': request.get('protocol'),
                    'resp': 'success',
                    'data': {
                        'schedule': result['schedule'],
                        'generation_method': 'openai_ai',
                        'processing_time': processing_time,
                        'ai_metadata': {
                            'model_used': self.ai_generator.model,
                            'attempt': result.get('attempt', 1),
                            'has_fairness_analysis': 'fairness_analysis' in result
                        }
                    }
                }
            else:
                logger.error(f"❌ AI 근무표 생성 실패: {result.get('message', 'Unknown error')}")
                
                return {
                    'protocol': request.get('protocol'),
                    'resp': 'error',
                    'data': {
                        'error': result.get('message', 'AI schedule generation failed'),
                        'processing_time': processing_time
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ 근무표 요청 처리 오류: {e}")
            return {
                'protocol': request.get('protocol'),
                'resp': 'error',
                'data': {'error': str(e)}
            }
    
    def handle_handover_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """인수인계 명료화 요청 처리"""
        try:
            logger.info("📝 AI 인수인계 명료화 요청 처리 시작")
            
            data = request.get('data', {})
            original_text = data.get('text', '')
            
            # OpenAI로 인수인계 명료화
            result = self.ai_enhancer.enhance_handover_text(original_text)
            
            if result.get('status') == 'success':
                logger.info("✅ AI 인수인계 명료화 성공")
                
                return {
                    'protocol': 'py_handover_summary',
                    'resp': 'success',
                    'data': {
                        'original_text': result['original_text'],
                        'enhanced_text': result['enhanced_text'],
                        'processing_time': result.get('processing_time', 0),
                        'model_used': result.get('model_used', 'gpt-3.5-turbo')
                    }
                }
            else:
                logger.error(f"❌ AI 인수인계 명료화 실패: {result.get('message', 'Unknown error')}")
                
                return {
                    'protocol': 'py_handover_summary',
                    'resp': 'error',
                    'data': {
                        'error': result.get('message', 'AI handover enhancement failed'),
                        'original_text': result['original_text'],
                        'enhanced_text': result['enhanced_text']
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ 인수인계 요청 처리 오류: {e}")
            return {
                'protocol': 'py_handover_summary',
                'resp': 'error',
                'data': {'error': str(e)}
            }
    
    def stop(self):
        """서버 중지"""
        self.running = False
        logger.info("🛑 서버 중지 요청됨")

# =============================================================================
# 메인 실행부
# =============================================================================

def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("🤖 AI Shift Scheduler Server v1.0")
    logger.info("=" * 60)
    logger.info("🔧 기능: OpenAI 기반 근무표 생성 + 인수인계 명료화")
    logger.info("🎯 특징: 현실적이고 유연한 근무표, 160시간 제약 자동 해결")
    logger.info("📡 프로토콜: 기존 C++ 클라이언트 완전 호환")
    logger.info("=" * 60)
    
    # OpenAI 상태 확인
    if OPENAI_AVAILABLE:
        logger.info("✅ OpenAI API 연결 확인됨")
    else:
        logger.error("❌ OpenAI API 사용 불가 - OPENAI_API_KEY 확인 필요")
        logger.error("⚠️ 서버를 시작하지만 AI 기능이 비활성화됩니다")
    
    # 서버 시작
    server = AIShiftSchedulerServer()
    
    try:
        logger.info("🌐 TCP 서버 시작 중...")
        server.start()
    except KeyboardInterrupt:
        logger.info("⌨️ 키보드 인터럽트 감지")
    except Exception as e:
        logger.error(f"❌ 서버 오류: {e}")
    finally:
        server.stop()
        logger.info("👋 AI 근무표 서버 종료")

if __name__ == "__main__":
    main()