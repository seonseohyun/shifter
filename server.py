#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
근무표 생성 및 인수인계 요약 TCP 서버
C++ 클라이언트와 TCP 통신 (리틀엔디안 방식)
"""

import socket
import struct
import json
import threading
import logging
import sys
import os
from datetime import datetime, timedelta
import calendar
from typing import Dict, List, Any, Tuple, Optional

# OR-Tools import
try:
    from ortools.sat.python import cp_model
except ImportError:
    print("ERROR: OR-Tools가 설치되어 있지 않습니다.")
    print("설치: pip install ortools")
    sys.exit(1)

# OpenAI import
try:
    from openai import OpenAI
except ImportError:
    print("ERROR: OpenAI 라이브러리가 설치되어 있지 않습니다.")
    print("설치: pip install openai")
    sys.exit(1)

# 환경 변수에서 OpenAI API 키 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("WARNING: python-dotenv가 설치되어 있지 않습니다.")
    print("설치: pip install python-dotenv")

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ScheduleGenerator:
    """OR-Tools를 사용한 근무표 생성 클래스"""
    
    def __init__(self):
        self.model = None
        self.solver = None
        
    def generate_schedule(self, staff_data: Dict, position: str, target_month: str, custom_rules: Dict) -> Dict[str, Any]:
        """근무표 생성 메인 함수"""
        try:
            logger.info(f"근무표 생성 시작: {position}, {target_month}")
            
            # 월 정보 파싱
            year, month = map(int, target_month.split('-'))
            days_in_month = calendar.monthrange(year, month)[1]
            
            # 직원 데이터 파싱
            staff_list = staff_data['staff']
            staff_count = len(staff_list)
            
            # 근무 시프트 정보
            shifts = custom_rules['shifts']
            shift_hours = custom_rules['shift_hours']
            
            logger.info(f"직원 수: {staff_count}, 일 수: {days_in_month}, 시프트: {shifts}")
            
            # OR-Tools 모델 생성
            model = cp_model.CpModel()
            
            # 변수 생성: schedule[staff_id, day, shift]
            schedule = {}
            for i, staff in enumerate(staff_list):
                staff_id = staff['staff_id']
                for day in range(days_in_month):
                    for shift in shifts:
                        schedule[(staff_id, day, shift)] = model.NewBoolVar(f'staff_{staff_id}_day_{day}_shift_{shift}')
            
            # 제약 조건 1: 각 직원은 하루에 하나의 시프트만
            for i, staff in enumerate(staff_list):
                staff_id = staff['staff_id']
                for day in range(days_in_month):
                    model.AddExactlyOne([schedule[(staff_id, day, shift)] for shift in shifts])
            
            # 제약 조건 2: 각 시프트마다 최소 인원 보장
            min_staff_per_shift = max(1, staff_count // len([s for s in shifts if s != 'Off']))
            for day in range(days_in_month):
                for shift in shifts:
                    if shift != 'Off':
                        model.Add(sum(schedule[(staff['staff_id'], day, shift)] for staff in staff_list) >= min_staff_per_shift)
            
            # 직군별 제약사항 적용
            self._apply_position_rules(model, schedule, staff_list, shifts, days_in_month, position, shift_hours)
            
            # 목적 함수: 근무 시간의 균등 분배
            staff_hours = []
            for staff in staff_list:
                staff_id = staff['staff_id']
                total_hours = sum(schedule[(staff_id, day, shift)] * shift_hours[shift] 
                                for day in range(days_in_month) for shift in shifts)
                staff_hours.append(total_hours)
            
            # 근무시간 편차 최소화
            max_hours = model.NewIntVar(0, 300, 'max_hours')
            min_hours = model.NewIntVar(0, 300, 'min_hours')
            
            for hours in staff_hours:
                model.Add(hours <= max_hours)
                model.Add(hours >= min_hours)
            
            model.Minimize(max_hours - min_hours)
            
            # 해결
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = 30.0
            status = solver.Solve(model)
            
            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                # 결과 생성
                result = self._build_schedule_result(solver, schedule, staff_list, shifts, year, month, days_in_month)
                logger.info("근무표 생성 완료")
                return {
                    "protocol": "py_gen_schedule",
                    "resp": "success",
                    "data": result
                }
            else:
                error_msg = f"근무표 생성 실패: 제약조건을 만족하는 해가 없습니다. (상태: {status})"
                logger.error(error_msg)
                return {
                    "protocol": "py_gen_schedule",
                    "resp": "fail",
                    "data": [],
                    "message": error_msg
                }
                
        except Exception as e:
            error_msg = f"근무표 생성 중 오류: {str(e)}"
            logger.error(error_msg)
            return {
                "protocol": "py_gen_schedule",
                "resp": "fail",
                "data": [],
                "message": error_msg
            }
    
    def _apply_position_rules(self, model, schedule, staff_list, shifts, days_in_month, position, shift_hours):
        """직군별 제약사항 적용"""
        rules = self._get_position_rules(position)
        
        for staff in staff_list:
            staff_id = staff['staff_id']
            grade = staff['grade']
            
            # 간호 직군 규칙
            if position == "간호":
                # 신규는 야간 금지 (grade 5가 신규라고 가정)
                if rules.get("newbie_no_night", False) and grade == 5:
                    for day in range(days_in_month):
                        if 'Night' in shifts:
                            model.Add(schedule[(staff_id, day, 'Night')] == 0)
                
                # 야간 다음날 데이 금지
                if rules.get("night_after_day", False) and 'Night' in shifts and 'Day' in shifts:
                    for day in range(days_in_month - 1):
                        night = schedule[(staff_id, day, 'Night')]
                        day_next = schedule[(staff_id, day + 1, 'Day')]
                        model.AddImplication(night, day_next.Not())
                
                # 최소 휴무일
                if "min_off_days" in rules and 'Off' in shifts:
                    min_off = rules["min_off_days"]
                    model.Add(sum(schedule[(staff_id, day, 'Off')] for day in range(days_in_month)) >= min_off)
                
                # 최대 월 근무시간
                if "max_monthly_hours" in rules:
                    max_hours = rules["max_monthly_hours"]
                    total_hours = sum(schedule[(staff_id, day, shift)] * shift_hours[shift] 
                                    for day in range(days_in_month) for shift in shifts)
                    model.Add(total_hours <= max_hours)
            
            # 소방 직군 규칙
            elif position == "소방":
                # D24 다음날 오프 필수
                if rules.get("night_after_off", False) and 'D24' in shifts and 'Off' in shifts:
                    for day in range(days_in_month - 1):
                        d24 = schedule[(staff_id, day, 'D24')]
                        off_next = schedule[(staff_id, day + 1, 'Off')]
                        model.AddImplication(d24, off_next)
                
                # 최대 월 근무시간
                if "max_monthly_hours" in rules:
                    max_hours = rules["max_monthly_hours"]
                    total_hours = sum(schedule[(staff_id, day, shift)] * shift_hours[shift] 
                                    for day in range(days_in_month) for shift in shifts)
                    model.Add(total_hours <= max_hours)
    
    def _get_position_rules(self, position: str) -> Dict:
        """직군별 규칙 반환"""
        rules = {
            "간호": {
                "min_off_days": 3,
                "newbie_no_night": True,
                "night_after_day": True,
                "max_monthly_hours": 209
            },
            "소방": {
                "shift_cycle": "3_day",
                "duty_per_cycle": 1,
                "max_monthly_hours": 192,
                "night_after_off": True
            },
            "기본": {
                "max_monthly_hours": 200
            }
        }
        return rules.get(position, rules["기본"])
    
    def _build_schedule_result(self, solver, schedule, staff_list, shifts, year, month, days_in_month) -> List[Dict]:
        """스케줄 결과 구성"""
        result = []
        
        for day in range(days_in_month):
            date_str = f"{year:04d}-{month:02d}-{day+1:02d}"
            
            for shift in shifts:
                if shift == 'Off':
                    continue
                    
                people = []
                for staff in staff_list:
                    staff_id = staff['staff_id']
                    if solver.Value(schedule[(staff_id, day, shift)]):
                        people.append({
                            "name": staff['name'],
                            "staff_id": staff_id,
                            "grade": staff['grade']
                        })
                
                if people:  # 해당 시프트에 배정된 사람이 있을 때만 추가
                    result.append({
                        "date": date_str,
                        "shift": shift,
                        "hours": 8,  # 기본 8시간
                        "people": people
                    })
        
        return result


class HandoverSummary:
    """OpenAI를 사용한 인수인계 요약 클래스"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """OpenAI 클라이언트 초기화"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
            return
        
        try:
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {e}")
    
    def summarize_handover(self, input_text: str) -> Dict[str, Any]:
        """인수인계 요약"""
        try:
            if not self.client:
                return {
                    "protocol": "res_handover_summary",
                    "data": {
                        "task": "summarize_handover",
                        "result": "OpenAI API 클라이언트가 초기화되지 않았습니다."
                    },
                    "resp": "fail"
                }
            
            logger.info("인수인계 요약 시작")
            
            prompt = """넌 Master Handover AI야.

간결하고 명확하게 인수인계 내용을 요약하는 전문가야.

입력된 내용을 빠르게 파악할 수 있도록 핵심만 뽑아 요약해줘.

중요한 일정, 변경사항, 위험요소는 우선순위로 정리하고,

불필요한 말은 생략하고 실무에 바로 도움이 되도록 써줘."""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": input_text}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            
            logger.info("인수인계 요약 완료")
            return {
                "protocol": "res_handover_summary",
                "data": {
                    "task": "summarize_handover",
                    "result": summary
                },
                "resp": "success"
            }
            
        except Exception as e:
            error_msg = f"인수인계 요약 중 오류: {str(e)}"
            logger.error(error_msg)
            return {
                "protocol": "res_handover_summary",
                "data": {
                    "task": "summarize_handover",
                    "result": error_msg
                },
                "resp": "fail"
            }


class TCPServer:
    """TCP 서버 메인 클래스"""
    
    def __init__(self, host='0.0.0.0', port=6004):
        self.host = host
        self.port = port
        self.schedule_generator = ScheduleGenerator()
        self.handover_summary = HandoverSummary()
        
    def start(self):
        """서버 시작"""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            
            logger.info(f"서버 시작: {self.host}:{self.port}")
            print(f"🚀 서버가 {self.host}:{self.port}에서 실행 중입니다...")
            
            while True:
                client_socket, addr = server_socket.accept()
                logger.info(f"클라이언트 연결: {addr}")
                
                # 각 클라이언트를 별도 스레드에서 처리
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            logger.info("서버 종료 중...")
            print("\n서버가 종료되었습니다.")
        except Exception as e:
            logger.error(f"서버 오류: {e}")
        finally:
            server_socket.close()
    
    def _handle_client(self, client_socket: socket.socket, addr):
        """클라이언트 요청 처리"""
        try:
            # 헤더 수신 (8바이트: total_size + json_size)
            header_data = self._recv_exact(client_socket, 8)
            if not header_data:
                return
            
            total_size = struct.unpack('<I', header_data[:4])[0]
            json_size = struct.unpack('<I', header_data[4:8])[0]
            
            logger.info(f"요청 헤더: total_size={total_size}, json_size={json_size}")
            
            # JSON 데이터 수신
            json_data = self._recv_exact(client_socket, json_size)
            if not json_data:
                return
            
            # UTF-8 디코딩 및 JSON 파싱
            try:
                request_str = json_data.decode('utf-8')
                logger.info(f"수신된 JSON (UTF-8): {request_str[:200]}...")
                request = json.loads(request_str)
            except UnicodeDecodeError as e:
                logger.error(f"UTF-8 디코딩 실패: {e}")
                raise Exception(f"UTF-8 디코딩 실패: {e}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {e}")
                raise Exception(f"JSON 파싱 실패: {e}")
            
            logger.info(f"요청 프로토콜: {request.get('protocol', 'Unknown')}")
            
            # 프로토콜에 따른 처리
            response = self._process_request(request)
            
            # 응답 전송
            self._send_response(client_socket, response)
            
        except Exception as e:
            logger.error(f"클라이언트 처리 오류 ({addr}): {e}")
            # 오류 응답 전송
            error_response = {
                "protocol": "error",
                "resp": "fail",
                "message": str(e)
            }
            self._send_response(client_socket, error_response)
        finally:
            client_socket.close()
            logger.info(f"클라이언트 연결 종료: {addr}")
    
    def _recv_exact(self, sock: socket.socket, n: int) -> bytes:
        """정확히 n바이트 수신"""
        buf = b''
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("연결이 종료됨")
            buf += chunk
        return buf
    
    def _send_response(self, client_socket: socket.socket, response: Dict):
        """응답 전송 (UTF-8 인코딩)"""
        try:
            # JSON 인코딩 (UTF-8, 유니코드 문자 보존)
            response_str = json.dumps(response, ensure_ascii=False, indent=None)
            logger.info(f"전송할 JSON (UTF-8): {response_str[:200]}...")
            
            # UTF-8로 인코딩
            response_bytes = response_str.encode('utf-8')
            
            total_size = len(response_bytes)
            json_size = len(response_bytes)
            
            # 리틀엔디안 헤더 생성 (C++ uint32_t 호환)
            header = struct.pack('<I', total_size) + struct.pack('<I', json_size)
            
            logger.info(f"응답 헤더 생성: total_size={total_size}, json_size={json_size}")
            
            # 헤더 + UTF-8 데이터 전송
            client_socket.sendall(header + response_bytes)
            
            logger.info(f"응답 전송 완료: {len(response_bytes)} 바이트 (UTF-8)")
            
        except UnicodeEncodeError as e:
            logger.error(f"UTF-8 인코딩 실패: {e}")
            # 오류 응답을 ASCII로 전송
            error_response = {
                "protocol": "error",
                "resp": "fail", 
                "message": f"UTF-8 encoding failed: {str(e)}"
            }
            error_str = json.dumps(error_response, ensure_ascii=True)
            error_bytes = error_str.encode('utf-8')
            header = struct.pack('<I', len(error_bytes)) + struct.pack('<I', len(error_bytes))
            client_socket.sendall(header + error_bytes)
        except Exception as e:
            logger.error(f"응답 전송 오류: {e}")
    
    def _process_request(self, request: Dict) -> Dict:
        """요청 처리"""
        protocol = request.get('protocol', '')
        
        if protocol == 'py_gen_timetable':
            # 근무표 생성 요청
            data = request.get('data', {})
            staff_data = data.get('staff_data', {})
            position = data.get('position', '기본')
            target_month = data.get('target_month', '')
            custom_rules = data.get('custom_rules', {})
            
            return self.schedule_generator.generate_schedule(
                staff_data, position, target_month, custom_rules
            )
            
        elif protocol == 'py_req_handover_summary':
            # 인수인계 요약 요청
            data = request.get('data', {})
            input_text = data.get('input_text', '')
            
            return self.handover_summary.summarize_handover(input_text)
            
        else:
            # 알 수 없는 프로토콜
            return {
                "protocol": "error",
                "resp": "fail",
                "message": f"알 수 없는 프로토콜: {protocol}"
            }


def main():
    """메인 함수"""
    server = TCPServer()
    server.start()


if __name__ == "__main__":
    main()