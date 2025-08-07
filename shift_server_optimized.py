#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimized Shift Scheduler Server
Single-file implementation with OR-Tools CP-SAT solver
Handles Korean encoding and nursing constraints
"""

import socket
import json
import logging
import calendar
import os
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from ortools.sat.python import cp_model

# OpenAI import (optional)
try:
    from openai import OpenAI
    from dotenv import load_dotenv
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# Configuration
HOST = '127.0.0.1'
PORT = 6004
SOLVER_TIMEOUT_SECONDS = 30.0

# Load environment variables
if OPENAI_AVAILABLE:
    load_dotenv()

# OpenAI configuration
openai_client = None
if OPENAI_AVAILABLE:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class SolverStatus(Enum):
    """Solver status enumeration"""
    OPTIMAL = "optimal"
    FEASIBLE = "feasible" 
    INFEASIBLE = "infeasible"
    UNKNOWN = "unknown"


@dataclass
class Staff:
    """Staff member data structure"""
    name: str
    staff_id: int
    grade: int
    total_hours: int
    position: str = "default"
    grade_name: Optional[str] = None
    
    def __post_init__(self):
        """Validate staff data after initialization"""
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
    """Shift rules configuration"""
    shifts: List[str]
    shift_hours: Dict[str, int]
    night_shifts: List[str]
    off_shifts: List[str]
    
    def __post_init__(self):
        """Validate shift rules after initialization"""
        if not self.shifts:
            raise ValueError("Shifts cannot be empty")
        
        # Check shift hours mapping
        missing_hours = [s for s in self.shifts if s not in self.shift_hours]
        if missing_hours:
            raise ValueError(f"Missing shift hours for: {missing_hours}")
        
        # Validate shift hours
        for shift, hours in self.shift_hours.items():
            if not isinstance(hours, (int, float)) or hours < 0 or hours > 24:
                raise ValueError(f"Invalid hours for shift '{shift}': {hours}")
        
        # Check if we have at least one working shift
        work_shifts = [s for s in self.shifts if self.shift_hours.get(s, 0) > 0]
        if not work_shifts:
            raise ValueError("No working shifts found (all shifts have 0 hours)")


@dataclass
class PositionRules:
    """Position-specific rules and constraints"""
    newbie_no_night: bool = False
    night_after_off: bool = True
    max_monthly_hours: int = 180
    newbie_grade: int = 5
    default_shifts: List[str] = field(default_factory=lambda: ['D', 'E', 'N', 'O'])
    default_shift_hours: Dict[str, int] = field(default_factory=lambda: {'D': 8, 'E': 8, 'N': 8, 'O': 0})
    default_night_shifts: List[str] = field(default_factory=lambda: ['N'])
    default_off_shifts: List[str] = field(default_factory=lambda: ['O'])


# Position-specific rule definitions
POSITION_RULES: Dict[str, PositionRules] = {
    "간호": PositionRules(
        newbie_no_night=True,
        night_after_off=True,
        max_monthly_hours=209,
        newbie_grade=5,
        default_shifts=['Day', 'Evening', 'Night', 'Off'],
        default_shift_hours={'Day': 8, 'Evening': 8, 'Night': 8, 'Off': 0},
        default_night_shifts=['Night'],
        default_off_shifts=['Off']
    ),
    "소방": PositionRules(
        night_after_off=True,
        max_monthly_hours=190,
        default_shifts=['D24', 'O'],
        default_shift_hours={'D24': 24, 'O': 0},
        default_night_shifts=['D24'],
        default_off_shifts=['O']
    ),
    "default": PositionRules()
}


class ShiftSchedulerError(Exception):
    """Custom exception for shift scheduler errors"""
    pass


def summarize_handover(input_text: str) -> Dict[str, Any]:
    """OpenAI를 활용한 인수인계 내용 요약"""
    start_time = time.time()
    
    try:
        # OpenAI 클라이언트 체크
        if openai_client is None:
            return {
                "status": "error",
                "task": "summarize_handover", 
                "reason": "OpenAI API 키가 설정되지 않았습니다."
            }
        
        # 입력 검증
        if not input_text or input_text.strip() == "":
            return {
                "status": "error",
                "task": "summarize_handover",
                "reason": "input_text가 비어 있습니다."
            }
        
        logger.info("=== 인수인계 요약 시작 ===")
        logger.info(f"입력 텍스트 길이: {len(input_text)} 문자")
        
        # Master Handover AI 프롬프트
        system_prompt = """넌 Master Handover AI야. 
간결하고 명확하게 인수인계 내용을 요약하는 전문가야.

입력된 내용을 빠르게 파악할 수 있도록 핵심만 뽑아 요약해줘.  
중요한 일정, 변경사항, 위험요소는 우선순위로 정리하고,  
불필요한 말은 생략하고 실무에 바로 도움이 되도록 써줘."""
        
        # OpenAI API 호출
        logger.info("OpenAI API 호출 중...")
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        process_time = time.time() - start_time
        
        logger.info(f"요약 완료: {process_time:.2f}초")
        logger.info(f"요약 결과 길이: {len(summary)} 문자")
        
        return {
            "status": "success",
            "task": "summarize_handover",
            "result": summary
        }
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"인수인계 요약 오류 ({process_time:.2f}초): {e}")
        return {
            "status": "error",
            "task": "summarize_handover", 
            "reason": f"요약 처리 중 오류 발생: {str(e)}"
        }


class RequestValidator:
    """Request validation utilities"""
    
    @staticmethod
    def validate_staff_data(staff_data: Dict[str, Any]) -> List[Staff]:
        """Validate and convert staff data to Staff objects"""
        if not staff_data or "staff" not in staff_data:
            raise ShiftSchedulerError("Missing staff_data.staff field")
        
        staff_list = staff_data["staff"]
        if not isinstance(staff_list, list) or len(staff_list) == 0:
            raise ShiftSchedulerError("Staff list is empty or invalid")
        
        validated_staff = []
        for i, person_data in enumerate(staff_list):
            try:
                # Handle field name variations (protocol compatibility)
                staff_id = person_data.get("staff_id") or person_data.get("staff_uid")
                total_hours = (person_data.get("total_hours") or 
                             person_data.get("total_monthly_work_hours") or
                             person_data.get("monthly_workhour", 0))
                
                if staff_id is None:
                    raise ValueError("Missing staff_id/staff_uid")
                
                staff = Staff(
                    name=person_data.get("name", f"Staff_{staff_id}"),
                    staff_id=int(staff_id),
                    grade=person_data.get("grade", 1),
                    total_hours=int(total_hours),
                    grade_name=person_data.get("grade_name")
                )
                validated_staff.append(staff)
                
            except (ValueError, TypeError, KeyError) as e:
                raise ShiftSchedulerError(f"Invalid staff data at index {i}: {e}")
        
        return validated_staff
    
    @staticmethod
    def validate_shift_rules(custom_rules: Dict[str, Any], position_rules: PositionRules) -> ShiftRules:
        """Validate and create shift rules"""
        if not custom_rules:
            # Use defaults from position rules
            return ShiftRules(
                shifts=position_rules.default_shifts,
                shift_hours=position_rules.default_shift_hours,
                night_shifts=position_rules.default_night_shifts,
                off_shifts=position_rules.default_off_shifts
            )
        
        shifts = custom_rules.get("shifts", position_rules.default_shifts)
        shift_hours = custom_rules.get("shift_hours", position_rules.default_shift_hours)
        
        # Explicit shift specification (preferred)
        night_shifts = custom_rules.get("night_shifts", [])
        off_shifts = custom_rules.get("off_shifts", [])
        
        # Auto-detection if not explicitly specified
        if not night_shifts and not off_shifts:
            night_shifts, off_shifts = RequestValidator._detect_shifts(shifts, position_rules)
        
        return ShiftRules(
            shifts=shifts,
            shift_hours=shift_hours,
            night_shifts=night_shifts,
            off_shifts=off_shifts
        )
    
    @staticmethod
    def _detect_shifts(shifts: List[str], position_rules: PositionRules) -> Tuple[List[str], List[str]]:
        """Auto-detect night and off shifts from shift names"""
        night_keywords = ['night', 'nocturnal', '야간', '밤', '심야']
        off_keywords = ['off', 'rest', 'free', '휴무', '쉼', '오프']
        
        night_abbrev = {'n': 'night', 'nt': 'night'}
        off_abbrev = {'o': 'off', 'r': 'rest'}
        
        detected_night = []
        detected_off = []
        
        logger.info(f"Auto-detecting shifts from: {shifts}")
        
        for shift in shifts:
            shift_lower = shift.lower()
            
            # Night shift detection
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
            
            # Off shift detection (only if not night)
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
        
        # Fallback to defaults if detection failed
        if not detected_night and not detected_off:
            detected_night = position_rules.default_night_shifts
            detected_off = position_rules.default_off_shifts
            logger.info(f"Using defaults: night={detected_night}, off={detected_off}")
        
        return detected_night, detected_off


class ShiftScheduler:
    """Main shift scheduling logic using OR-Tools CP-SAT"""
    
    def __init__(self, staff: List[Staff], shift_rules: ShiftRules, 
                 position: str, num_days: int):
        self.staff = staff
        self.shift_rules = shift_rules  
        self.position = position
        self.num_days = num_days
        self.position_rules = POSITION_RULES.get(position, POSITION_RULES["default"])
        
        # Create CP model
        self.model = cp_model.CpModel()
        self.schedule = {}
        self._create_variables()
        
    def _create_variables(self):
        """Create decision variables for the schedule"""
        for staff_member in self.staff:
            staff_id = str(staff_member.staff_id)
            for day in range(self.num_days):
                for shift in self.shift_rules.shifts:
                    var_name = f'schedule_{staff_id}_{day}_{shift}'
                    self.schedule[(staff_id, day, shift)] = self.model.NewBoolVar(var_name)
    
    def _apply_basic_constraints(self):
        """Apply basic scheduling constraints"""
        # Each work shift must have at least one person assigned daily
        for day in range(self.num_days):
            for shift in self.shift_rules.shifts:
                if shift not in self.shift_rules.off_shifts:
                    shift_vars = [self.schedule[(str(staff.staff_id), day, shift)] 
                                for staff in self.staff]
                    self.model.Add(sum(shift_vars) >= 1)
        
        # Each person works exactly one shift per day
        for staff_member in self.staff:
            staff_id = str(staff_member.staff_id)
            for day in range(self.num_days):
                day_shifts = [self.schedule[(staff_id, day, shift)] 
                            for shift in self.shift_rules.shifts]
                self.model.Add(sum(day_shifts) == 1)
    
    def _apply_position_constraints(self):
        """Apply position-specific constraints"""
        logger.info(f"Applying {self.position} position constraints")
        
        for staff_member in self.staff:
            staff_id = str(staff_member.staff_id)
            
            # Monthly working hours limit
            work_hours = []
            for day in range(self.num_days):
                for shift in self.shift_rules.shifts:
                    hours = self.shift_rules.shift_hours.get(shift, 0)
                    if hours > 0:
                        work_hours.append(self.schedule[(staff_id, day, shift)] * hours)
            
            if work_hours:
                monthly_limit = min(staff_member.total_hours, 
                                  self.position_rules.max_monthly_hours)
                self.model.Add(sum(work_hours) <= monthly_limit)
            
            # Newbie no night shift constraint (nursing)
            if (self.position == "간호" and 
                self.position_rules.newbie_no_night and
                staff_member.grade == self.position_rules.newbie_grade):
                
                for night_shift in self.shift_rules.night_shifts:
                    if night_shift in self.shift_rules.shifts:
                        for day in range(self.num_days):
                            self.model.Add(self.schedule[(staff_id, day, night_shift)] == 0)
                logger.info(f"{staff_member.name}: Newbie night shift restriction applied")
            
            # Night shift followed by off constraint
            if (self.position_rules.night_after_off and 
                self.shift_rules.night_shifts and 
                self.shift_rules.off_shifts):
                
                for day in range(self.num_days - 1):
                    night_vars = [self.schedule[(staff_id, day, ns)] 
                                for ns in self.shift_rules.night_shifts 
                                if ns in self.shift_rules.shifts]
                    off_next_vars = [self.schedule[(staff_id, day + 1, os)] 
                                   for os in self.shift_rules.off_shifts 
                                   if os in self.shift_rules.shifts]
                    
                    if night_vars and off_next_vars:
                        total_night = sum(night_vars)
                        total_off_next = sum(off_next_vars)
                        # If working night, must be off next day
                        self.model.Add(total_night <= total_off_next)
                        
                        # Additional constraint: no other work shifts after night
                        for other_shift in self.shift_rules.shifts:
                            if (other_shift not in self.shift_rules.off_shifts and 
                                other_shift not in self.shift_rules.night_shifts):
                                next_shift = self.schedule[(staff_id, day + 1, other_shift)]
                                for night_var in night_vars:
                                    self.model.AddBoolOr([night_var.Not(), next_shift.Not()])
    
    def _apply_firefighter_constraints(self):
        """Apply firefighter-specific constraints"""
        if self.position != "소방":
            return
        
        logger.info("Applying firefighter constraints")
        
        # Identify duty shifts (24-hour shifts)
        duty_shifts = [s for s in self.shift_rules.shifts 
                      if any(keyword in s.lower() for keyword in ['d24', '24', '당직'])]
        if not duty_shifts:
            duty_shifts = self.shift_rules.night_shifts  # Fallback
        
        if duty_shifts and self.shift_rules.off_shifts and self.num_days >= 3:
            logger.info(f"Firefighter duty shifts: {duty_shifts}")
            
            for staff_member in self.staff:
                staff_id = str(staff_member.staff_id)
                
                # 24-hour duty followed by at least 1 day off
                for day in range(self.num_days - 1):
                    duty_vars = [self.schedule[(staff_id, day, ds)] 
                               for ds in duty_shifts 
                               if ds in self.shift_rules.shifts]
                    off_next_vars = [self.schedule[(staff_id, day + 1, os)] 
                                   for os in self.shift_rules.off_shifts 
                                   if os in self.shift_rules.shifts]
                    
                    if duty_vars and off_next_vars:
                        total_duty = sum(duty_vars)
                        total_off_next = sum(off_next_vars)
                        self.model.Add(total_duty <= total_off_next)
                
                # Monthly duty count limits (6-15 times)
                monthly_duty_count = []
                for day in range(self.num_days):
                    for duty_shift in duty_shifts:
                        if duty_shift in self.shift_rules.shifts:
                            monthly_duty_count.append(self.schedule[(staff_id, day, duty_shift)])
                
                if monthly_duty_count:
                    self.model.Add(sum(monthly_duty_count) <= 15)
                    self.model.Add(sum(monthly_duty_count) >= 6)
    
    def solve(self) -> Tuple[SolverStatus, Optional[Dict]]:
        """Solve the scheduling problem"""
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
        """Extract and format the solution"""
        schedule_data = []
        
        for day in range(self.num_days):
            for shift in self.shift_rules.shifts:
                people = []
                for staff_member in self.staff:
                    staff_id = str(staff_member.staff_id)
                    if solver.Value(self.schedule[(staff_id, day, shift)]):
                        people.append({
                            "name": staff_member.name,
                            "staff_id": staff_member.staff_id,
                            "grade": staff_member.grade
                        })
                
                if people:  # Only include shifts with assigned people
                    schedule_data.append({
                        "day": day,
                        "shift": shift,
                        "hours": self.shift_rules.shift_hours.get(shift, 0),
                        "people": people
                    })
        
        return {"schedule": schedule_data}


class ShiftSchedulerServer:
    """TCP server for shift scheduling requests"""
    
    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self.socket = None
    
    def start(self):
        """Start the TCP server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            logger.info(f"Shift scheduler server started on {self.host}:{self.port}")
            
            while True:
                try:
                    conn, addr = self.socket.accept()
                    self._handle_client(conn, addr)
                except KeyboardInterrupt:
                    logger.info("Server shutdown requested")
                    break
                except Exception as e:
                    logger.error(f"Connection accept error: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Server start error: {e}")
        finally:
            if self.socket:
                self.socket.close()
                logger.info("Server socket closed")
    
    def _handle_client(self, conn: socket.socket, addr: Tuple[str, int]):
        """Handle individual client connection"""
        try:
            logger.info(f"Client connected: {addr}")
            
            # Receive data
            data = b''
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
            
            if not data:
                logger.warning(f"Empty request from {addr}")
                return
            
            # Parse JSON with encoding fallback
            request_data = self._parse_json_with_encoding(data, addr)
            if request_data is None:
                self._send_error_response(conn, "Failed to parse request")
                return
            
            # Process request
            response = self._process_request(request_data)
            
            # Send response
            response_json = json.dumps(response, ensure_ascii=False, indent=2)
            conn.sendall(response_json.encode('utf-8'))
            
            logger.info(f"Response sent to {addr}: {response.get('resp', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Client handling error {addr}: {e}")
            self._send_error_response(conn, str(e))
        finally:
            conn.close()
    
    def _parse_json_with_encoding(self, data: bytes, addr: Tuple[str, int]) -> Optional[Dict[str, Any]]:
        """Parse JSON with multiple encoding attempts"""
        encodings = ['utf-8', 'cp949', 'latin-1']
        
        for encoding in encodings:
            try:
                decoded_text = data.decode(encoding)
                request_data = json.loads(decoded_text)
                logger.info(f"Successfully decoded with {encoding}")
                return request_data
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        
        logger.error(f"All encoding attempts failed for {addr}")
        return None
    
    def _send_error_response(self, conn: socket.socket, error_message: str):
        """Send error response to client"""
        try:
            error_response = {
                "protocol": "py_gen_schedule",
                "resp": "fail", 
                "data": [],
                "error": error_message
            }
            response_json = json.dumps(error_response, ensure_ascii=False)
            conn.sendall(response_json.encode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")
    
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
                    return summarize_handover(input_text)
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
            # Add position to all staff members
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
                # Convert solution to date-based format
                schedule_data = self._format_schedule_response(
                    solution["schedule"], start_date
                )
                
                return {
                    "protocol": "py_gen_schedule",
                    "resp": "success",
                    "data": schedule_data
                }
            else:
                return {
                    "protocol": "py_gen_schedule",
                    "resp": "fail",
                    "data": [],
                    "reason": "No feasible schedule found"
                }
        
        except ShiftSchedulerError as e:
            logger.error(f"Validation error: {e}")
            return {
                "protocol": "py_gen_schedule",
                "resp": "fail",
                "data": [],
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return {
                "protocol": "py_gen_schedule", 
                "resp": "fail",
                "data": [],
                "error": "Internal server error"
            }
    
    def _parse_target_month(self, target_month: Optional[str]) -> Tuple[datetime, int]:
        """Parse target month string and return start date and number of days"""
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
        """Format schedule data with proper date strings"""
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


if __name__ == "__main__":
    main()