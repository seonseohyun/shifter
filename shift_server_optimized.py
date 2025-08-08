#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimized Shift Scheduler Server
Single-file implementation with OR-Tools CP-SAT solver
Handles Korean encoding and nursing constraints
"""

import socket
import json
import struct
import logging
import calendar
import os
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from pathlib import Path
from ortools.sat.python import cp_model

from dotenv import load_dotenv
from openai import OpenAI

# Configuration
HOST = '0.0.0.0'
PORT = 6004
SOLVER_TIMEOUT_SECONDS = 30.0

# Load environment variables
load_dotenv()

# OpenAI configuration
openai_client = None
OPENAI_AVAILABLE = True
if OPENAI_AVAILABLE:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    else:
        print("OPENAI_API_KEY is not set in .env file or environment variables.")
else:
    print("OpenAI is not available.")

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class SolverStatus(Enum):
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    UNKNOWN = "unknown"

@dataclass
class Staff:
    name: str
    staff_id: int
    grade: int
    total_hours: int
    position: str = "default"
    grade_name: Optional[str] = None
    def __post_init__(self):
        if not self.name or not isinstance(self.name, str):
            raise ValueError(f"Invalid staff name: {self.name}")
        if not isinstance(self.staff_id, int) or self.staff_id <= 0:
            raise ValueError(f"Invalid staff_id: {self.staff_id}")
        if not isinstance(self.grade, int) or self.grade <= 0:
            raise ValueError(f"Invalid grade: {self.grade}")
        if not isinstance(self.total_hours, (int, float)) or self.total_hours < 0:
            raise ValueError(f"Invalid total_hours: {self.total_hours}")

@dataclass
class ShiftRules:
    shifts: List[str]
    shift_hours: Dict[str, int]
    night_shifts: List[str]
    off_shifts: List[str]
    def __post_init__(self):
        if not self.shifts:
            raise ValueError("Shifts cannot be empty")
        missing_hours = [s for s in self.shifts if s not in self.shift_hours]
        if missing_hours:
            raise ValueError(f"Missing shift hours for: {missing_hours}")
        for shift, hours in self.shift_hours.items():
            if not isinstance(hours, (int, float)) or hours < 0 or hours > 24:
                raise ValueError(f"Invalid hours for shift '{shift}': {hours}")
        work_shifts = [s for s in self.shifts if self.shift_hours.get(s, 0) > 0]
        if not work_shifts:
            raise ValueError("No working shifts found (all shifts have 0 hours)")

@dataclass
class PositionRules:
    newbie_no_night: bool = False
    night_after_off: bool = True
    max_monthly_hours: int = 180
    newbie_grade: int = 5
    default_shifts: List[str] = field(default_factory=lambda: ['D', 'E', 'N', 'O'])
    default_shift_hours: Dict[str, int] = field(default_factory=lambda: {'D': 8, 'E': 8, 'N': 8, 'O': 0})
    default_night_shifts: List[str] = field(default_factory=lambda: ['N'])
    default_off_shifts: List[str] = field(default_factory=lambda: ['O'])

POSITION_RULES = {
    "간호": PositionRules(newbie_no_night=True, night_after_off=True, max_monthly_hours=209, newbie_grade=5, default_shifts=['Day', 'Evening', 'Night', 'Off'], default_shift_hours={'Day': 8, 'Evening': 8, 'Night': 8, 'Off': 0}, default_night_shifts=['Night'], default_off_shifts=['Off']),
    "소방": PositionRules(night_after_off=True, max_monthly_hours=190, default_shifts=['D24', 'O'], default_shift_hours={'D24': 24, 'O': 0}, default_night_shifts=['D24'], default_off_shifts=['O']),
    "default": PositionRules()
}

class ShiftSchedulerError(Exception):
    pass

class ResponseLogger:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self._ensure_data_directory()
    def _ensure_data_directory(self):
        try:
            self.data_dir.mkdir(exist_ok=True)
            logger.debug(f"Data directory ensured: {self.data_dir}")
        except OSError as e:
            logger.error(f"Failed to create data directory {self.data_dir}: {e}")
            raise
    def _generate_filename(self, request_type: str, timestamp: datetime) -> str:
        datetime_str = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"{request_type}_response_{datetime_str}.json"
    def _save_response(self, response_data: Dict[str, Any], request_type: str, timestamp: datetime, additional_metadata: Optional[Dict[str, Any]] = None) -> bool:
        try:
            filename = self._generate_filename(request_type, timestamp)
            filepath = self.data_dir / filename
            log_entry = {"timestamp": timestamp.isoformat(), "request_type": request_type, "response_data": response_data}
            if additional_metadata:
                log_entry["metadata"] = additional_metadata
            with filepath.open('w', encoding='utf-8') as f:
                json.dump(log_entry, f, ensure_ascii=False, indent=2)
            logger.info(f"Response logged successfully: {filepath}")
            return True
        except (OSError, IOError, TypeError) as e:
            logger.error(f"Failed to save {request_type} response: {e}")
            return False
        except json.JSONEncodeError as e:
            logger.error(f"JSON encoding error for {request_type} response: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving {request_type} response: {e}")
            return False
    def log_schedule_response(self, response_data: Dict[str, Any], timestamp: Optional[datetime] = None, staff_count: Optional[int] = None, position: Optional[str] = None, target_month: Optional[str] = None) -> bool:
        if timestamp is None:
            timestamp = datetime.now()
        metadata = {}
        if staff_count is not None:
            metadata["staff_count"] = staff_count
        if position is not None:
            metadata["position"] = position
        if target_month is not None:
            metadata["target_month"] = target_month
        return self._save_response(response_data=response_data, request_type="schedule", timestamp=timestamp, additional_metadata=metadata if metadata else None)
    def log_handover_response(self, response_data: Dict[str, Any], timestamp: Optional[datetime] = None, input_text_length: Optional[int] = None, processing_time: Optional[float] = None) -> bool:
        if timestamp is None:
            timestamp = datetime.now()
        metadata = {}
        if input_text_length is not None:
            metadata["input_text_length"] = input_text_length
        if processing_time is not None:
            metadata["processing_time_seconds"] = processing_time
        return self._save_response(response_data=response_data, request_type="handover", timestamp=timestamp, additional_metadata=metadata if metadata else None)

def summarize_handover(input_text: str) -> Dict[str, Any]:
    start_time = time.time()
    try:
        if openai_client is None:
            return {"status": "error", "task": "summarize_handover", "reason": "OpenAI API 키가 설정되지 않았습니다."}
        if not input_text or input_text.strip() == "":
            return {"status": "error", "task": "summarize_handover", "reason": "input_text가 비어 있습니다."}
        logger.info("=== 인수인계 요약 시작 ===")
        logger.info(f"입력 텍스트 길이: {len(input_text)} 문자")
        system_prompt = """넌 Master Handover AI야. 
간결하고 명확하게 인수인계 내용을 요약하는 전문가야.

입력된 내용을 빠르게 파악할 수 있도록 핵심만 뽑아 요약해줘.  
중요한 일정, 변경사항, 위험요소는 우선순위로 정리하고,  
불필요한 말은 생략하고 실무에 바로 도움이 되도록 써줘."""
        logger.info("OpenAI API 호출 중...")
        response = openai_client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": input_text}], max_tokens=1000, temperature=0.3)
        summary = response.choices[0].message.content.strip()
        process_time = time.time() - start_time
        logger.info(f"요약 완료: {process_time:.2f}초")
        logger.info(f"요약 결과 길이: {len(summary)} 문자")
        return {"status": "success", "task": "summarize_handover", "result": summary}
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"인수인계 요약 오류 ({process_time:.2f}초): {e}")
        return {"status": "error", "task": "summarize_handover", "reason": f"요약 처리 중 오류 발생: {str(e)}"}

class RequestValidator:
    @staticmethod
    def validate_staff_data(staff_data: Dict[str, Any]) -> List[Staff]:
        if not staff_data or "staff" not in staff_data:
            raise ShiftSchedulerError("Missing staff_data.staff field")
        staff_list = staff_data["staff"]
        if not isinstance(staff_list, list) or len(staff_list) == 0:
            raise ShiftSchedulerError("Staff list is empty or invalid")
        validated_staff = []
        for i, person_data in enumerate(staff_list):
            try:
                staff_id = person_data.get("staff_id") or person_data.get("staff_uid")
                total_hours = (person_data.get("total_hours") or person_data.get("total_monthly_work_hours") or person_data.get("monthly_workhour", 0))
                if staff_id is None:
                    raise ValueError("Missing staff_id/staff_uid")
                staff = Staff(name=person_data.get("name", f"Staff_{staff_id}"), staff_id=int(staff_id), grade=person_data.get("grade", 1), total_hours=int(total_hours), grade_name=person_data.get("grade_name"))
                validated_staff.append(staff)
            except (ValueError, TypeError, KeyError) as e:
                raise ShiftSchedulerError(f"Invalid staff data at index {i}: {e}")
        return validated_staff
    @staticmethod
    def validate_shift_rules(custom_rules: Dict[str, Any], position_rules: PositionRules) -> ShiftRules:
        if not custom_rules:
            return ShiftRules(shifts=position_rules.default_shifts, shift_hours=position_rules.default_shift_hours, night_shifts=position_rules.default_night_shifts, off_shifts=position_rules.default_off_shifts)
        shifts = custom_rules.get("shifts", position_rules.default_shifts)
        shift_hours = custom_rules.get("shift_hours", position_rules.default_shift_hours)
        night_shifts = custom_rules.get("night_shifts", [])
        off_shifts = custom_rules.get("off_shifts", [])
        if not night_shifts and not off_shifts:
            night_shifts, off_shifts = RequestValidator._detect_shifts(shifts, position_rules)
        return ShiftRules(shifts=shifts, shift_hours=shift_hours, night_shifts=night_shifts, off_shifts=off_shifts)
    @staticmethod
    def _detect_shifts(shifts: List[str], position_rules: PositionRules) -> Tuple[List[str], List[str]]:
        night_keywords = ['night', 'nocturnal', '야간', '밤', '심야']
        off_keywords = ['off', 'rest', 'free', '휴무', '쉼', '오프']
        night_abbrev = {'n': 'night', 'nt': 'night'}
        off_abbrev = {'o': 'off', 'r': 'rest'}
        detected_night = []
        detected_off = []
        logger.info(f"Auto-detecting shifts from: {shifts}")
        for shift in shifts:
            shift_lower = shift.lower()
            is_night = False
            if shift_lower in night_abbrev:
                detected_night.append(shift)
                is_night = True
                logger.info(f"'{shift}' -> Night (abbreviation)")
            else:
                for keyword in night_keywords:
                    if keyword.lower() in shift_lower and len(keyword) >= 3:
                        detected_night.append(shift)
                        is_night = True
                        logger.info(f"'{shift}' -> Night (keyword: {keyword})")
                        break
            if not is_night:
                if shift_lower in off_abbrev:
                    detected_off.append(shift)
                    logger.info(f"'{shift}' -> Off (abbreviation)")
                else:
                    for keyword in off_keywords:
                        if keyword.lower() in shift_lower and len(keyword) >= 3:
                            detected_off.append(shift)
                            logger.info(f"'{shift}' -> Off (keyword: {keyword})")
                            break
        if not detected_night and not detected_off:
            detected_night = position_rules.default_night_shifts
            detected_off = position_rules.default_off_shifts
            logger.info(f"Using defaults: night={detected_night}, off={detected_off}")
        return detected_night, detected_off

class ShiftScheduler:
    def __init__(self, staff: List[Staff], shift_rules: ShiftRules, position: str, num_days: int):
        self.staff = staff
        self.shift_rules = shift_rules  
        self.position = position
        self.num_days = num_days
        self.position_rules = POSITION_RULES.get(position, POSITION_RULES["default"])
        self.model = cp_model.CpModel()
        self.schedule = {}
        self._create_variables()
    def _create_variables(self):
        for staff_member in self.staff:
            staff_id = str(staff_member.staff_id)
            for day in range(self.num_days):
                for shift in self.shift_rules.shifts:
                    var_name = f'schedule_{staff_id}_{day}_{shift}'
                    self.schedule[(staff_id, day, shift)] = self.model.NewBoolVar(var_name)
    def _apply_basic_constraints(self):
        for day in range(self.num_days):
            for shift in self.shift_rules.shifts:
                if shift not in self.shift_rules.off_shifts:
                    shift_vars = [self.schedule[(str(staff.staff_id), day, shift)] for staff in self.staff]
                    self.model.Add(sum(shift_vars) >= 1)
        for staff_member in self.staff:
            staff_id = str(staff_member.staff_id)
            for day in range(self.num_days):
                day_shifts = [self.schedule[(staff_id, day, shift)] for shift in self.shift_rules.shifts]
                self.model.Add(sum(day_shifts) == 1)
    def _apply_position_constraints(self):
        logger.info(f"Applying {self.position} position constraints")
        for staff_member in self.staff:
            staff_id = str(staff_member.staff_id)
            work_hours = []
            for day in range(self.num_days):
                for shift in self.shift_rules.shifts:
                    hours = self.shift_rules.shift_hours.get(shift, 0)
                    if hours > 0:
                        work_hours.append(self.schedule[(staff_id, day, shift)] * hours)
            if work_hours:
                monthly_limit = min(staff_member.total_hours, self.position_rules.max_monthly_hours)
                self.model.Add(sum(work_hours) <= monthly_limit)
            if self.position == "간호" and self.position_rules.newbie_no_night and staff_member.grade == self.position_rules.newbie_grade:
                for night_shift in self.shift_rules.night_shifts:
                    if night_shift in self.shift_rules.shifts:
                        for day in range(self.num_days):
                            self.model.Add(self.schedule[(staff_id, day, night_shift)] == 0)
                logger.info(f"{staff_member.name}: Newbie night shift restriction applied")
            if self.position_rules.night_after_off and self.shift_rules.night_shifts and self.shift_rules.off_shifts:
                for day in range(self.num_days - 1):
                    night_vars = [self.schedule[(staff_id, day, ns)] for ns in self.shift_rules.night_shifts if ns in self.shift_rules.shifts]
                    off_next_vars = [self.schedule[(staff_id, day + 1, os)] for os in self.shift_rules.off_shifts if os in self.shift_rules.shifts]
                    if night_vars and off_next_vars:
                        total_night = sum(night_vars)
                        total_off_next = sum(off_next_vars)
                        self.model.Add(total_night <= total_off_next)
                        for other_shift in self.shift_rules.shifts:
                            if other_shift not in self.shift_rules.off_shifts and other_shift not in self.shift_rules.night_shifts:
                                next_shift = self.schedule[(staff_id, day + 1, other_shift)]
                                for night_var in night_vars:
                                    self.model.AddBoolOr([night_var.Not(), next_shift.Not()])
    def _apply_firefighter_constraints(self):
        if self.position != "소방":
            return
        logger.info("Applying firefighter constraints")
        duty_shifts = [s for s in self.shift_rules.shifts if any(keyword in s.lower() for keyword in ['d24', '24', '당직'])]
        if not duty_shifts:
            duty_shifts = self.shift_rules.night_shifts
        if duty_shifts and self.shift_rules.off_shifts and self.num_days >= 3:
            logger.info(f"Firefighter duty shifts: {duty_shifts}")
            for staff_member in self.staff:
                staff_id = str(staff_member.staff_id)
                for day in range(self.num_days - 1):
                    duty_vars = [self.schedule[(staff_id, day, ds)] for ds in duty_shifts if ds in self.shift_rules.shifts]
                    off_next_vars = [self.schedule[(staff_id, day + 1, os)] for os in self.shift_rules.off_shifts if os in self.shift_rules.shifts]
                    if duty_vars and off_next_vars:
                        total_duty = sum(duty_vars)
                        total_off_next = sum(off_next_vars)
                        self.model.Add(total_duty <= total_off_next)
                monthly_duty_count = []
                for day in range(self.num_days):
                    for duty_shift in duty_shifts:
                        if duty_shift in self.shift_rules.shifts:
                            monthly_duty_count.append(self.schedule[(staff_id, day, duty_shift)])
                if monthly_duty_count:
                    self.model.Add(sum(monthly_duty_count) <= 15)
                    self.model.Add(sum(monthly_duty_count) >= 6)
    def solve(self) -> Tuple[SolverStatus, Optional[Dict]]:
        logger.info("Applying constraints...")
        self._apply_basic_constraints()
        self._apply_position_constraints()  
        self._apply_firefighter_constraints()
        logger.info("Starting CP-SAT solver...")
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = SOLVER_TIMEOUT_SECONDS
        status = solver.Solve(self.model)
        if status == cp_model.OPTIMAL:
            logger.info("Optimal solution found")
            return SolverStatus.OPTIMAL, self._extract_solution(solver)
        elif status == cp_model.FEASIBLE:
            logger.info("Feasible solution found")
            return SolverStatus.FEASIBLE, self._extract_solution(solver)
        elif status == cp_model.INFEASIBLE:
            logger.warning("No feasible solution found")
            return SolverStatus.INFEASIBLE, None
        else:
            logger.error(f"Solver failed with status: {solver.StatusName(status)}")
            return SolverStatus.UNKNOWN, None
    def _extract_solution(self, solver: cp_model.CpSolver) -> Dict[str, Any]:
        schedule_data = []
        for day in range(self.num_days):
            for shift in self.shift_rules.shifts:
                people = []
                for staff_member in self.staff:
                    staff_id = str(staff_member.staff_id)
                    if solver.Value(self.schedule[(staff_id, day, shift)]):
                        people.append({"name": staff_member.name, "staff_id": staff_member.staff_id, "grade": staff_member.grade})
                if people:
                    schedule_data.append({"day": day, "shift": shift, "hours": self.shift_rules.shift_hours.get(shift, 0), "people": people})
        return {"schedule": schedule_data}

class ShiftSchedulerServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 6004):
        self.host = host
        self.port = port
        self.server_socket = None
        self.response_logger = ResponseLogger()

    def recv_exact(self, conn: socket.socket, n: int) -> bytes:
        buf = b''
        while len(buf) < n:
            chunk = conn.recv(n - len(buf))
            if not chunk:
                raise ConnectionError(f"소켓 연결 끊김: {conn.getpeername()}")
            buf += chunk
        return buf

    def receive_packet(self, conn: socket.socket) -> tuple[Optional[Dict[str, Any]], list]:
        try:
            header = self.recv_exact(conn, 8)
            total_size = struct.unpack('>I', header[:4])[0]
            json_size = struct.unpack('>I', header[4:8])[0]
            logger.debug(f"Received header - totalSize: {total_size}, jsonSize: {json_size}")

            if json_size == 0 or json_size > total_size or total_size > 10 * 1024 * 1024:
                logger.error(f"헤더 정보 비정상: jsonSize={json_size}, totalSize={total_size}")
                return None, []

            buffer = self.recv_exact(conn, total_size)
            json_data = buffer[:json_size].decode('utf-8', errors='ignore')
            while json_data and ord(json_data[0]) in (0xC0, 0xC1) or ord(json_data[0]) < 0x20:
                logger.warning(f"JSON 앞에 비정상 바이트(0x{ord(json_data[0]):x}) 발견 → 제거")
                json_data = json_data[1:]

            try:
                request_data = json.loads(json_data)
                logger.info(f"Successfully parsed JSON from {conn.getpeername()}")
                return request_data, buffer[json_size:]
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {e}")
                return None, []

        except Exception as e:
            logger.error(f"패킷 처리 중 오류 발생 {conn.getpeername()}: {e}")
            return None, []

    def send_json_response(self, conn: socket.socket, json_str: str):
        json_bytes = json_str.encode('utf-8')
        total_size = len(json_bytes)
        header = struct.pack('>I', total_size) + struct.pack('>I', total_size)
        conn.sendall(header + json_bytes)
        logger.debug(f"Sent response to {conn.getpeername()}: {json_str}")

    def _process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process request with task-based routing"""
        try:
            start_time = datetime.now()

            # 1. Check for task-based requests (handover summarization)
            if "task" in request_data:
                task = request_data.get("task", "")
                logger.info(f"Processing task request: {task}")
                
                if task == "summarize_handover":
                    input_text = request_data.get("input_text", "")
                    process_start = datetime.now()
                    response = summarize_handover(input_text)
                    process_time = (datetime.now() - process_start).total_seconds()
                    
                    # Log handover response
                    self.response_logger.log_handover_response(
                        response_data=response,
                        timestamp=process_start,
                        input_text_length=len(input_text) if input_text else None,
                        processing_time=process_time
                    )
                    
                    return response
                else:
                    return {
                        "status": "error",
                        "task": task,
                        "reason": f"Unknown task: {task}"
                    }
            
            # 2. Handle protocol wrapper if present (schedule generation)
            if "protocol" in request_data and "data" in request_data:
                protocol = request_data.get("protocol", "")
                actual_data = request_data.get("data", {})
                logger.info(f"Processing protocol request: {protocol}")
            else:
                actual_data = request_data
            
            # Extract request parameters
            staff_data = actual_data.get("staff_data", {})
            position = actual_data.get("position", "default")
            target_month = actual_data.get("target_month", None)
            custom_rules = actual_data.get("custom_rules", {})
            
            logger.info(f"Processing schedule request for position: {position}")
            
            # Validate and parse data
            staff = RequestValidator.validate_staff_data(staff_data)
            for staff_member in staff:
                staff_member.position = position
            
            position_rules = POSITION_RULES.get(position, POSITION_RULES["default"])
            shift_rules = RequestValidator.validate_shift_rules(custom_rules, position_rules)
            
            logger.info(f"Staff count: {len(staff)}")
            logger.info(f"Shifts: {shift_rules.shifts}")
            logger.info(f"Night shifts: {shift_rules.night_shifts}")
            logger.info(f"Off shifts: {shift_rules.off_shifts}")
            
            # Parse target month
            start_date, num_days = self._parse_target_month(target_month)
            
            # Create and solve schedule
            scheduler = ShiftScheduler(staff, shift_rules, position, num_days)
            status, solution = scheduler.solve()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Processing completed in {processing_time:.2f} seconds")
            
            # Format response
            if status in [SolverStatus.OPTIMAL, SolverStatus.FEASIBLE]:
                schedule_data = self._format_schedule_response(solution["schedule"], start_date)
                response = {
                    "protocol": "py_gen_schedule",
                    "resp": "success",
                    "data": schedule_data
                }
                self.response_logger.log_schedule_response(response, start_time, len(staff), position, target_month)
                return response
            else:
                response = {
                    "protocol": "py_gen_schedule",
                    "resp": "fail",
                    "data": [],
                    "reason": "No feasible schedule found"
                }
                self.response_logger.log_schedule_response(response, start_time, len(staff), position, target_month)
                return response
        
        except ShiftSchedulerError as e:
            logger.error(f"Validation error: {e}")
            error_response = {
                "protocol": "py_gen_schedule",
                "resp": "fail",
                "data": [],
                "error": str(e)
            }
            self.response_logger.log_schedule_response(error_response, datetime.now(), None, position, target_month)
            return error_response
        except Exception as e:
            logger.error(f"Processing error: {e}")
            error_response = {
                "protocol": "py_gen_schedule",
                "resp": "fail",
                "data": [],
                "error": "Internal server error"
            }
            self.response_logger.log_schedule_response(error_response, datetime.now(), None, position, target_month)
            return error_response

    def _parse_target_month(self, target_month: Optional[str]) -> Tuple[datetime, int]:
        try:
            if target_month:
                year, month = map(int, target_month.split('-'))
            else:
                now = datetime.now()
                year, month = now.year, now.month
            start_date = datetime(year, month, 1)
            num_days = calendar.monthrange(year, month)[1]
            logger.info(f"Target month: {year}-{month:02d} ({num_days} days)")
            return start_date, num_days
        except Exception as e:
            logger.warning(f"Target month parsing error: {e}, using default")
            return datetime(2025, 9, 1), 30

    def _format_schedule_response(self, schedule: List[Dict], start_date: datetime) -> List[Dict]:
        formatted_schedule = []
        for entry in schedule:
            date_str = (start_date + timedelta(days=entry["day"])).strftime('%Y-%m-%d')
            formatted_entry = {
                "date": date_str,
                "shift": entry["shift"],
                "hours": entry["hours"],
                "people": entry["people"]
            }
            formatted_schedule.append(formatted_entry)
        return formatted_schedule

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        logger.info(f"Shift scheduler server started on {self.host}:{self.port}")

        while True:
            conn, addr = self.server_socket.accept()
            logger.info(f"Client connected: {addr}")
            try:
                request_data, _ = self.receive_packet(conn)
                if request_data is not None:
                    response = self._process_request(request_data)
                    response_json = json.dumps(response, ensure_ascii=False)
                    self.send_json_response(conn, response_json)
            except Exception as e:
                logger.error(f"Client handling error {addr}: {e}")
                self.send_json_response(conn, json.dumps({"resp": "fail", "error": str(e)}))
            finally:
                conn.close()

def main():
    """Main server entry point"""
    logger.info("Starting Optimized Shift Scheduler Server")
    
    server = ShiftSchedulerServer()
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        logger.info("Server shutdown complete")
        if server.server_socket:
            server.server_socket.close()

if __name__ == "__main__":
    main()