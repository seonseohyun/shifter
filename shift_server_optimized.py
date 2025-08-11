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
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S', force=True)
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
        except OSError as e:
            logger.error(f"Failed to create data directory {self.data_dir}: {e}")
            raise
    def _generate_filename(self, request_type: str, timestamp: datetime) -> str:
        datetime_str = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"{request_type}_response_{datetime_str}.json"
    def _save_response(self, response_data: Dict[str, Any], request_type: str, timestamp: datetime, additional_metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save response data to file with comprehensive error handling.
        
        Args:
            response_data: The response data to save
            request_type: Type of request for filename generation
            timestamp: Timestamp for the request
            additional_metadata: Optional additional metadata to include
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            filename = self._generate_filename(request_type, timestamp)
            filepath = self.data_dir / filename
            
            # Initialize log entry with timestamp and request type
            log_entry = {
                "timestamp": timestamp.isoformat(),
                "request_type": request_type
            }
            
            # Merge response_data directly into log_entry
            log_entry.update(response_data)
            
            # Add additional metadata if provided
            if additional_metadata:
                log_entry.update(additional_metadata)
            
            # Write to file with proper encoding and formatting
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

class BinaryProtocolHandler:
    """
    Binary protocol handler for C++ client compatibility.
    
    C++ Protocol Format:
    - 8-byte header: totalSize (4 bytes, little-endian) + jsonSize (4 bytes, little-endian)
    - JSON data: UTF-8 encoded string
    
    IMPORTANT: Uses little-endian format for x86/x64 compatibility.
    Big-endian clients will cause parsing errors and should be fixed at the client side.
    """
    
    MAX_PACKET_SIZE = 10 * 1024 * 1024  # 10MB limit
    
    @staticmethod
    def create_endian_error_response() -> Dict[str, Any]:
        """
        Create a standardized error response for endian mismatch issues.
        """
        return {
            "status": "error",
            "protocol": "binary_protocol_error",
            "error_type": "endian_mismatch",
            "message": "Client is using big-endian format. Server requires little-endian format for x86 compatibility.",
            "solution": "Update client to use little-endian format (struct.pack('<I', value)) instead of big-endian.",
            "technical_details": {
                "expected_format": "little-endian uint32_t (x86 standard)",
                "detected_format": "big-endian uint32_t (network byte order)",
                "header_size": 8,
                "max_packet_size": BinaryProtocolHandler.MAX_PACKET_SIZE
            }
        }
    
    @staticmethod  
    def recv_exact(conn: socket.socket, n: int) -> bytes:
        """Receive exactly n bytes from socket."""
        conn.settimeout(5.0)  # 5초 타임아웃
        buf = b''
        while len(buf) < n:
            chunk = conn.recv(n - len(buf))
            if not chunk:
                raise ConnectionError(f"Socket connection closed unexpectedly from {conn.getpeername()}")
            buf += chunk
        return buf

    @staticmethod
    def receive_packet(conn: socket.socket) -> tuple[Optional[Dict[str, Any]], Optional[bytes]]:
        """
        Receive packet using C++ binary protocol.
        Returns: (parsed_json_dict, payload_bytes) or (None, None) on error
        """
        try:
            # 1. Read 8-byte header
            header = BinaryProtocolHandler.recv_exact(conn, 8)
            
            # 2. Parse header (little-endian uint32_t)
            total_size = struct.unpack('<I', header[:4])[0]  # Changed from '>I' to '<I'
            json_size = struct.unpack('<I', header[4:8])[0]  # Changed from '>I' to '<I'
            

            # 3. Validate header with enhanced endian mismatch detection
            if json_size == 0 or json_size > total_size or total_size > BinaryProtocolHandler.MAX_PACKET_SIZE:
                logger.error(f"[BINARY] 🚨 Invalid header from {conn.getpeername()}: jsonSize={json_size}, totalSize={total_size}")
                
                # Check if this might be a big-endian mismatch
                if total_size > 1000000:  # Suspiciously large value suggests endian mismatch
                    try:
                        # Try interpreting the header as big-endian to see if it makes sense
                        big_total_size = struct.unpack('>I', header[:4])[0]
                        big_json_size = struct.unpack('>I', header[4:8])[0]
                        
                        if big_total_size < 10000 and big_json_size <= big_total_size and big_json_size > 0:
                            logger.error(f"[BINARY] 🔄 ENDIAN MISMATCH DETECTED!")
                            logger.error(f"[BINARY] If interpreted as big-endian: totalSize={big_total_size}, jsonSize={big_json_size}")
                            logger.error(f"[BINARY] Client is sending big-endian data but server expects little-endian!")
                            logger.error(f"[BINARY] 🔧 FIX: Client must use little-endian format (x86 standard)")
                        
                    except struct.error:
                        pass
                
                return None, None

            # 4. Read data
            if total_size == 0:
                logger.warning(f"[BINARY] Zero-length data from {conn.getpeername()}")
                return None, None
                
            buffer = BinaryProtocolHandler.recv_exact(conn, total_size)
            
            # 5. Extract JSON data
            json_data = buffer[:json_size].decode('utf-8', errors='ignore')
            
            # 6. Clean invalid UTF-8 bytes and BOM (as C++ code does)
            while json_data and (
                (ord(json_data[0]) == 0xC0) or 
                (ord(json_data[0]) == 0xC1) or 
                (ord(json_data[0]) < 0x20)
            ):
                logger.warning(f"[BINARY] Removing invalid byte 0x{ord(json_data[0]):02x} from JSON start")
                json_data = json_data[1:]

            # 7. Parse JSON
            try:
                request_data = json.loads(json_data)
                logger.info(f"[BINARY] Successfully parsed JSON from {conn.getpeername()}")
                
                # 8. Extract payload if any
                payload = buffer[json_size:] if json_size < total_size else None
                
                return request_data, payload
                
            except json.JSONDecodeError as e:
                logger.error(f"[BINARY] JSON parsing failed from {conn.getpeername()}: {e}")
                return None, None

        except ConnectionError as e:
            logger.error(f"[BINARY] Connection error from {conn.getpeername()}: {e}")
            return None, None
        except struct.error as e:
            logger.error(f"[BINARY] Header unpacking error from {conn.getpeername()}: {e}")
            return None, None
        except Exception as e:
            logger.error(f"[BINARY] Unexpected error receiving packet from {conn.getpeername()}: {e}")
            return None, None

    @staticmethod
    def send_json_response(conn: socket.socket, json_str: str):
        """
        Send JSON response using C++ binary protocol.
        
        Format:
        - 8-byte header: totalSize (4 bytes) + jsonSize (4 bytes), both little-endian
        - JSON data: UTF-8 encoded string
        """
        try:
            json_bytes = json_str.encode('utf-8')
            total_size = len(json_bytes)
            json_size = len(json_bytes)
            
            # Create 8-byte header (little-endian uint32_t)
            header = struct.pack('<I', total_size) + struct.pack('<I', json_size)  # Changed from '>I' to '<I'
            
            # Send header + data
            conn.sendall(header + json_bytes)
            
            
        except Exception as e:
            logger.error(f"[BINARY] Failed to send response to {conn.getpeername()}: {e}")
            raise


class LegacyProtocolHandler:
    """
    Legacy protocol handler for Python clients (JSON only, no headers).
    Uses EOF to determine message boundaries.
    """
    
    @staticmethod
    def receive_json(conn: socket.socket) -> Optional[Dict[str, Any]]:
        """Receive JSON data without headers (legacy Python client mode)."""
        try:
            # Set a reasonable timeout for legacy connections
            conn.settimeout(5.0)
            
            data = b''
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                # Try to parse JSON to see if we have a complete message
                try:
                    json_str = data.decode('utf-8')
                    request_data = json.loads(json_str)
                    logger.info(f"[LEGACY] Successfully parsed JSON from {conn.getpeername()}")
                    return request_data
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue  # Keep reading
                    
        except socket.timeout:
            logger.warning(f"[LEGACY] Timeout receiving data from {conn.getpeername()}")
        except Exception as e:
            logger.error(f"[LEGACY] Error receiving JSON from {conn.getpeername()}: {e}")
        
        return None

    @staticmethod
    def send_json_response(conn: socket.socket, json_str: str):
        """Send JSON response without headers (legacy Python client mode)."""
        try:
            json_bytes = json_str.encode('utf-8')
            conn.sendall(json_bytes)
        except Exception as e:
            logger.error(f"[LEGACY] Failed to send response to {conn.getpeername()}: {e}")
            raise


class ShiftSchedulerServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 6004):
        self.host = host
        self.port = port
        self.server_socket = None
        self.response_logger = ResponseLogger()

    def detect_protocol_type(self, conn: socket.socket) -> str:
        """
        Enhanced protocol detection with endian mismatch handling.
        
        Method:
        - Peek at first 8 bytes without consuming them
        - Try little-endian interpretation first (correct format)
        - If invalid, check for big-endian mismatch and log warning
        - Otherwise, assume legacy JSON protocol
        """
        try:
            # Peek at first 8 bytes
            header_peek = conn.recv(8, socket.MSG_PEEK)
            
            if len(header_peek) < 8:
                return "legacy"
            
            # Try to interpret as little-endian binary header (correct format)
            try:
                total_size = struct.unpack('<I', header_peek[:4])[0]
                json_size = struct.unpack('<I', header_peek[4:8])[0]
                
                # Validate header values for little-endian
                if (json_size > 0 and 
                    json_size <= total_size and 
                    total_size <= BinaryProtocolHandler.MAX_PACKET_SIZE and
                    total_size < 1000000):  # Reasonable size for typical requests
                    
                    return "binary"
                
                # Check for potential big-endian mismatch
                try:
                    big_total_size = struct.unpack('>I', header_peek[:4])[0]
                    big_json_size = struct.unpack('>I', header_peek[4:8])[0]
                    
                    # If big-endian interpretation gives reasonable values, it's likely an endian mismatch
                    if (big_json_size > 0 and 
                        big_json_size <= big_total_size and 
                        big_total_size < 10000):  # Reasonable size when interpreted as big-endian
                        
                        logger.error(f"[PROTOCOL] 🚨 ENDIAN MISMATCH detected from {conn.getpeername()}! ")
                        logger.error(f"[PROTOCOL] Client sent big-endian header: totalSize={big_total_size}, jsonSize={big_json_size}")
                        logger.error(f"[PROTOCOL] Server interpreted as little-endian: totalSize={total_size}, jsonSize={json_size}")
                        logger.error(f"[PROTOCOL] Client must use little-endian format for x86 compatibility!")
                        
                        # Return special endian_error type for proper handling
                        return "endian_error"
                        
                except struct.error:
                    pass
                
                # Neither interpretation gives valid values
                return "legacy"
                    
            except struct.error:
                return "legacy"
                
        except Exception as e:
            logger.warning(f"[PROTOCOL] Protocol detection error from {conn.getpeername()}: {e}, defaulting to legacy")
            return "legacy"


    def _is_handover_request(self, request_data: Dict[str, Any]) -> bool:
        """인수인계 요청인지 확인"""
        # 직접 요청: {"task": "summarize_handover", "input_text": "..."}
        if "task" in request_data and request_data.get("task") == "summarize_handover":
            return True
        
        # 프로토콜 래퍼 요청: {"protocol": "py_req_handover_summary", "data": {"task": "summarize_handover", "input_text": "..."}}
        if "protocol" in request_data and "data" in request_data:
            data = request_data.get("data", {})
            if "task" in data and data.get("task") == "summarize_handover":
                return True
        
        return False
    
    def _is_schedule_request(self, request_data: Dict[str, Any]) -> bool:
        """근무표 생성 요청인지 확인"""
        # 프로토콜 래퍼가 있는 경우 확인
        if "protocol" in request_data and "data" in request_data:
            protocol = request_data.get("protocol", "")
            # py_gen_timetable 프로토콜은 근무표 생성 요청
            if protocol == "py_gen_timetable":
                return True
            # 인수인계 요청이 아니면 근무표 요청으로 간주
            return not self._is_handover_request(request_data)
        
        # 직접 요청에서 task가 없거나 알 수 없는 task가 아니면 근무표 요청으로 간주
        if "task" not in request_data:
            return True
        
        task = request_data.get("task", "")
        if task != "summarize_handover":
            return True
        
        return False
    
    def _process_handover_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """인수인계 명료화 전용 처리 함수"""
        try:
            start_time = datetime.now()
            
            # 프로토콜 래퍼 요청인지 확인
            is_protocol_wrapper = "protocol" in request_data and "data" in request_data
            
            if is_protocol_wrapper:
                # 프로토콜 래퍼 요청: {"protocol": "py_req_handover_summary", "data": {"task": "summarize_handover", "input_text": "..."}}
                protocol = request_data.get("protocol", "")
                actual_data = request_data.get("data", {})
                input_text = actual_data.get("input_text", "")
                
                logger.info(f"🎯 프로토콜 래퍼 인수인계 요청 처리: {protocol}")
            else:
                # 직접 요청: {"task": "summarize_handover", "input_text": "..."}
                input_text = request_data.get("input_text", "")
                
                logger.info("🎯 직접 인수인계 요청 처리")
            
            # 인수인계 요약 실행
            process_start = datetime.now()
            handover_result = summarize_handover(input_text)
            process_time = (datetime.now() - process_start).total_seconds()
            
            # 응답 형식 결정
            if is_protocol_wrapper:
                # 프로토콜 래퍼 응답: {"protocol": "res_handover_summary", "data": {"task": "summarize_handover", "result": "..."}, "resp": "success"}
                if handover_result.get("status") == "success":
                    response = {
                        "protocol": "res_handover_summary",
                        "data": {
                            "task": "summarize_handover",
                            "result": handover_result.get("result", "")
                        },
                        "resp": "success"
                    }
                else:
                    response = {
                        "protocol": "res_handover_summary",
                        "data": {
                            "task": "summarize_handover",
                            "result": handover_result.get("reason", "Unknown error")
                        },
                        "resp": "fail"
                    }
            else:
                # 직접 응답: {"status": "success", "task": "summarize_handover", "result": "..."}
                response = handover_result
            
            # 로깅
            self.response_logger.log_handover_response(
                response_data=response,
                timestamp=process_start,
                input_text_length=len(input_text) if input_text else None,
                processing_time=process_time
            )
            
            logger.info(f"✅ 인수인계 처리 완료 ({process_time:.2f}초)")
            return response
            
        except Exception as e:
            logger.error(f"❌ 인수인계 처리 오류: {e}")
            
            # 오류 응답 형식도 요청 형식에 맞춰 결정
            is_protocol_wrapper = "protocol" in request_data and "data" in request_data
            
            if is_protocol_wrapper:
                return {
                    "protocol": "res_handover_summary",
                    "data": {
                        "task": "summarize_handover",
                        "result": f"처리 중 오류 발생: {str(e)}"
                    },
                    "resp": "fail"
                }
            else:
                return {
                    "status": "error",
                    "task": "summarize_handover",
                    "reason": f"처리 중 오류 발생: {str(e)}"
                }
    
    def _process_schedule_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """근무표 생성 전용 처리 함수"""
        try:
            start_time = datetime.now()
            
            # 프로토콜 래퍼가 있는지 확인
            if "protocol" in request_data and "data" in request_data:
                actual_data = request_data.get("data", {})
                logger.info(f"📝 프로토콜 래퍼 근무표 요청 처리: {request_data.get('protocol', '')}")
            else:
                actual_data = request_data
                logger.info("📝 직접 근무표 요청 처리")
            
            # 직접 요청에서 알 수 없는 task가 있는 경우 오류 반환
            if "task" in request_data and request_data.get("task") != "":
                task = request_data.get("task")
                if task != "summarize_handover":  # 인수인계가 아닌 다른 task인 경우
                    logger.warning(f"⚠️ 알 수 없는 task: {task}")
                    return {
                        "status": "error",
                        "task": task,
                        "reason": f"Unknown task: {task}"
                    }
            
            # 근무표 생성을 위한 데이터 추출
            staff_data = actual_data.get("staff_data", {})
            position = actual_data.get("position", "default")
            target_month = actual_data.get("target_month", None)
            custom_rules = actual_data.get("custom_rules", {})
            
            logger.info(f"근무표 생성 요청 - 직책: {position}")
            
            # 데이터 검증 및 파싱
            staff = RequestValidator.validate_staff_data(staff_data)
            for staff_member in staff:
                staff_member.position = position
            
            position_rules = POSITION_RULES.get(position, POSITION_RULES["default"])
            shift_rules = RequestValidator.validate_shift_rules(custom_rules, position_rules)
            
            logger.info(f"직원 수: {len(staff)}")
            logger.info(f"근무 형태: {shift_rules.shifts}")
            logger.info(f"야간 근무: {shift_rules.night_shifts}")
            logger.info(f"휴무: {shift_rules.off_shifts}")
            
            # 대상 월 파싱
            start_date, num_days = self._parse_target_month(target_month)
            
            # 스케줄러 생성 및 실행
            scheduler = ShiftScheduler(staff, shift_rules, position, num_days)
            status, solution = scheduler.solve()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"근무표 생성 완료: {processing_time:.2f}초")
            
            # 응답 형식 결정
            if status in [SolverStatus.OPTIMAL, SolverStatus.FEASIBLE]:
                schedule_data = self._format_schedule_response(solution["schedule"], start_date)
                response = {
                    "protocol": "py_gen_schedule",
                    "resp": "success",
                    "data": schedule_data
                }
                logger.info(f"✅ 근무표 생성 성공 ({len(schedule_data)}개 항목)")
            else:
                response = {
                    "protocol": "py_gen_schedule",
                    "resp": "fail",
                    "data": []
                }
                logger.warning("⚠️ 실행 가능한 근무표를 찾을 수 없음")
            
            # 로깅
            self.response_logger.log_schedule_response(
                response, start_time, len(staff), position, target_month
            )
            
            return response
            
        except ShiftSchedulerError as e:
            logger.error(f"❌ 근무표 데이터 검증 오류: {e}")
            error_response = {
                "protocol": "py_gen_schedule",
                "resp": "fail",
                "data": []
            }
            try:
                position = request_data.get("data", {}).get("position", "unknown") if "data" in request_data else request_data.get("position", "unknown")
                target_month = request_data.get("data", {}).get("target_month", None) if "data" in request_data else request_data.get("target_month", None)
                self.response_logger.log_schedule_response(error_response, datetime.now(), None, position, target_month)
            except:
                pass  # 로깅 오류는 무시
            return error_response
            
        except Exception as e:
            logger.error(f"❌ 근무표 생성 내부 오류: {e}")
            error_response = {
                "protocol": "py_gen_schedule",
                "resp": "fail",
                "data": []
            }
            try:
                position = request_data.get("data", {}).get("position", "unknown") if "data" in request_data else request_data.get("position", "unknown")
                target_month = request_data.get("data", {}).get("target_month", None) if "data" in request_data else request_data.get("target_month", None)
                self.response_logger.log_schedule_response(error_response, datetime.now(), None, position, target_month)
            except:
                pass  # 로깅 오류는 무시
            return error_response
    
    def _process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """요청 타입에 따른 라우팅 및 처리"""
        try:
            logger.info(f"📨 요청 처리 시작 - 요청 키: {list(request_data.keys())}")
            
            # 요청 타입 식별 및 적절한 처리 함수로 라우팅
            if self._is_handover_request(request_data):
                logger.info("🎯 인수인계 요청으로 식별됨")
                return self._process_handover_request(request_data)
            
            elif self._is_schedule_request(request_data):
                logger.info("📝 근무표 생성 요청으로 식별됨")
                return self._process_schedule_request(request_data)
            
            else:
                # 식별되지 않는 요청 타입
                logger.warning(f"⚠️ 알 수 없는 요청 타입: {request_data}")
                return {
                    "status": "error",
                    "reason": "Unknown request type",
                    "supported_types": [
                        "handover: {task: 'summarize_handover', input_text: '...'}",
                        "schedule: {staff_data: {...}, position: '...', target_month: '...'}"
                    ]
                }
                
        except Exception as e:
            logger.error(f"❌ 요청 라우팅 오류: {e}")
            return {
                "status": "error",
                "reason": f"Request routing error: {str(e)}"
            }

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

    def _handle_client(self, conn: socket.socket, addr: tuple):
        """Handle individual client connection with protocol detection."""
        logger.info(f"Client connected: {addr}")
        
        try:

            #소켓 타임아웃 설정( 예: 5초)
            conn.settimeout(5.0)
            # Detect protocol type
            protocol_type = self.detect_protocol_type(conn)
            logger.info(f"[{addr}] Detected protocol: {protocol_type}")
            
            # Receive request based on protocol
            if protocol_type == "binary":
                request_data, _ = BinaryProtocolHandler.receive_packet(conn)
            elif protocol_type == "endian_error":
                # Special case: detected endian mismatch, send error and close
                logger.warning(f"[{addr}] Endian mismatch detected - consuming invalid header and sending error response")
                
                try:
                    # First, consume the invalid header that was peeked
                    invalid_header = conn.recv(8)
                    
                    # Create and send endian error response
                    endian_error = BinaryProtocolHandler.create_endian_error_response()
                    error_json = json.dumps(endian_error, ensure_ascii=False)
                    
                    # Send as legacy protocol (no binary headers)
                    LegacyProtocolHandler.send_json_response(conn, error_json)
                    logger.info(f"[{addr}] Endian mismatch error response sent successfully")
                    
                except Exception as e:
                    logger.error(f"[{addr}] Failed to handle endian error: {e}")
                    try:
                        # Fallback error response
                        fallback_error = json.dumps({"error": "Protocol error - use little-endian format"}, ensure_ascii=False)
                        LegacyProtocolHandler.send_json_response(conn, fallback_error)
                    except Exception as fallback_error:
                        logger.error(f"[{addr}] Fallback error response also failed: {fallback_error}")
                
                return  # Exit early, don't process further
            else:  # legacy
                request_data = LegacyProtocolHandler.receive_json(conn)
            
            if request_data is not None:
                # Process the request
                response = self._process_request(request_data)
                # JSON 문자열로 변환 (ensure_ascii=False로 한글 등 유지)
                response_json = json.dumps(response, ensure_ascii=False)
                
                # Send response based on protocol
                if protocol_type == "binary":
                    BinaryProtocolHandler.send_json_response(conn, response_json)
                else:  # legacy
                    LegacyProtocolHandler.send_json_response(conn, response_json)
                
                logger.info(f"[{addr}] Request processed successfully using {protocol_type} protocol")
            else:
                logger.warning(f"[{addr}] Failed to receive valid request data - possible endian mismatch")
                
                # Check if we should send a specific endian error response
                # This could happen if protocol detection failed due to endian issues
                if protocol_type == "binary":
                    # For binary protocol failures, send detailed endian error
                    endian_error = BinaryProtocolHandler.create_endian_error_response()
                    error_response = json.dumps(endian_error, ensure_ascii=False)
                else:
                    # For legacy protocol, send generic error
                    error_response = json.dumps({"resp": "fail", "error": "Invalid request data"}, ensure_ascii=False)
                
                try:
                    if protocol_type == "binary":
                        BinaryProtocolHandler.send_json_response(conn, error_response)
                    else:
                        LegacyProtocolHandler.send_json_response(conn, error_response)
                except Exception as send_error:
                    logger.error(f"[{addr}] Failed to send error response: {send_error}")
                    # Try legacy as fallback
                    try:
                        fallback_error = json.dumps({"resp": "fail", "error": "Protocol error"}, ensure_ascii=False) 
                        LegacyProtocolHandler.send_json_response(conn, fallback_error)
                    except Exception as fallback_error:
                        logger.error(f"[{addr}] Fallback error response also failed: {fallback_error}")
                    
        except Exception as e:
            logger.error(f"[{addr}] Client handling error: {e}")
            try:
                # Try to send error response with enhanced error details
                error_response = json.dumps({
                    "resp": "fail", 
                    "error": "Internal server error",
                    "hint": "If using binary protocol, ensure little-endian format is used"
                }, ensure_ascii=False)
                
                # Try both protocols to ensure delivery
                try:
                    BinaryProtocolHandler.send_json_response(conn, error_response)
                except Exception:
                    # Fallback to legacy protocol
                    LegacyProtocolHandler.send_json_response(conn, error_response)
                    
            except Exception as send_error:
                logger.error(f"[{addr}] Failed to send error response: {send_error}")
        finally:
            try:
                conn.close()
            except Exception as close_error:
                logger.error(f"[{addr}] Error closing connection: {close_error}")

    def start(self):
        """Start the server and listen for connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        logger.info(f"Shift scheduler server started on {self.host}:{self.port}")
        logger.info("Server supports both binary protocol (C++) and legacy protocol (Python)")
        logger.info("Binary protocol uses little-endian format for x86/x64 compatibility")
        logger.info("Enhanced endian mismatch detection and error reporting enabled")

        while True:
            try:
                conn, addr = self.server_socket.accept()
                self._handle_client(conn, addr)
            except KeyboardInterrupt:
                logger.info("Server shutdown requested by user")
                break
            except Exception as e:
                logger.error(f"Error accepting client connection: {e}")
                continue

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