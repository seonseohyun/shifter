# 최적화된 근무 스케줄러 서버: 주요 함수 및 클래스 설명

이 문서는 Python으로 구현된 **최적화된 근무 스케줄러 서버**의 주요 클래스와 함수를 상세히 설명합니다. 이 서버는 OR-Tools CP-SAT 솔버를 활용하여 간호 및 소방 직원의 근무 스케줄을 생성하며, C++와 Python 클라이언트를 위한 바이너리/레거시 JSON 프로토콜을 지원하고, OpenAI API로 인수인계 텍스트를 요약합니다. 문서는 목적, 입력/출력, 주요 로직, 용도를 중심으로 구성되었으며, 깔끔한 가독성과 버전 관리 호환성을 위해 Markdown 형식으로 작성되었습니다.

---

## 1. 주요 클래스와 역할

### 1.1 `Staff` (데이터 클래스)

- **목적**: 스케줄링에 필요한 직원 정보를 나타냅니다.
- **속성**:
  - `name: str`: 직원의 이름.
  - `staff_id: int`: 직원의 고유 식별자.
  - `grade: int`: 직원의 등급 (예: 경력 수준).
  - `total_hours: int`: 해당 월에 허용된 총 근무 시간.
  - `position: str`: 직원의 직책 (기본값: "default").
  - `grade_name: Optional[str]`: 직원의 등급 이름 (선택적).
- **주요 로직**:
  - `__post_init__`: 입력 데이터의 유효성을 검사합니다. 예를 들어, 이름이 비어 있거나 `staff_id`가 0 이하인 경우 `ValueError`를 발생시킵니다.
- **용도**: 스케줄러가 직원별 근무를 배정할 때 필요한 기본 정보를 제공합니다.

### 1.2 `ShiftRules` (데이터 클래스)

- **목적**: 근무 스케줄링에 사용되는 근무 유형과 규칙을 정의합니다.
- **속성**:
  - `shifts: List[str]`: 가능한 근무 유형 목록 (예: `['Day', 'Evening', 'Night', 'Off']`).
  - `shift_hours: Dict[str, int]`: 각 근무 유형의 근무 시간 (예: `{'Day': 8, 'Off': 0}`).
  - `night_shifts: List[str]`: 야간 근무로 간주되는 근무 유형.
  - `off_shifts: List[str]`: 휴무로 간주되는 근무 유형.
- **주요 로직**:
  - `__post_init__`: 근무 유형과 시간의 유효성을 검사합니다. 모든 근무 유형에 대해 시간이 정의되어야 하며, 근무 시간이 0~24시간 사이여야 합니다.
- **용도**: 스케줄러가 근무 배정을 위해 준수해야 할 규칙을 제공합니다.

### 1.3 `PositionRules` (데이터 클래스)

- **목적**: 간호, 소방 등 직책별 스케줄링 규칙을 정의합니다.
- **속성**:
  - `newbie_no_night: bool`: 신입 직원의 야간 근무 금지 여부.
  - `night_after_off: bool`: 야간 근무 후 휴무가 필요한지 여부.
  - `max_monthly_hours: int`: 월별 최대 근무 시간.
  - `newbie_grade: int`: 신입 직원으로 간주되는 등급.
  - `min_off_days: int`: 최소 휴무일 수.
  - `max_off_days: Optional[int]`: 최대 휴무일 수 (형평성 보장).
  - `min_work_days: Optional[int]`: 최소 근무일 수.
  - `default_shifts: List[str]`: 기본 근무 유형.
  - `default_shift_hours: Dict[str, int]`: 기본 근무 시간.
  - `default_night_shifts: List[str]`: 기본 야간 근무.
  - `default_off_shifts: List[str]`: 기본 휴무.
- **용도**: 직책별 특수 제약 조건을 적용합니다 (예: 간호 신입의 야간 근무 금지).

### 1.4 `ResponseLogger`

- **목적**: 서버의 응답(근무표 생성 또는 인수인계 요약)을 JSON 파일로 기록합니다.
- **주요 메서드**:
  - `_ensure_data_directory()`: 데이터 저장용 디렉토리를 생성합니다.
  - `_generate_filename(request_type: str, timestamp: datetime) -> str`: 요청 유형과 타임스탬프 기반으로 파일명을 생성합니다.
  - `_save_response(response_data: Dict[str, Any], request_type: str, timestamp: datetime, additional_metadata: Optional[Dict[str, Any]]) -> bool`: 응답 데이터를 JSON 파일로 저장하며, 메타데이터(직원 수, 처리 시간 등)를 포함합니다.
  - `log_schedule_response(...)`: 근무표 생성 응답을 기록합니다.
  - `log_handover_response(...)`: 인수인계 요약 응답을 기록합니다.
- **용도**: 디버깅 및 추적을 위해 서버 응답을 기록합니다.

### 1.5 `ShiftScheduler`

- **목적**: OR-Tools CP-SAT 솔버를 사용하여 제약 조건을 만족하는 근무 스케줄을 생성합니다.
- **주요 메서드**:
  - `__init__(staff: List[Staff], shift_rules: ShiftRules, position: str, num_days: int)`: 스케줄러를 초기화하고 직원-일-근무 조합 변수를 생성합니다.
  - `_create_variables()`: 각 직원의 날짜별 근무 배정을 위한 불리언 변수를 생성합니다.
  - `_apply_basic_constraints()`: 기본 제약 조건을 적용합니다 (예: 하루에 한 직원은 한 근무만 배정, 각 근무는 최소 한 명 배정).
  - `_apply_position_constraints()`: 직책별 제약 조건을 적용합니다 (예: 신입 야간 근무 금지, 최소/최대 휴무일).
  - `_apply_firefighter_constraints()`: 소방 직원 전용 제약 조건을 적용합니다 (예: 당직 후 휴무, 월별 당직 횟수 제한).
  - `solve() -> Tuple[SolverStatus, Optional[Dict]]`: 스케줄을 생성하고 결과를 반환합니다.
  - `_extract_solution(solver: cp_model.CpSolver) -> Dict[str, Any]`: 솔버 결과를 스케줄 데이터로 변환합니다.
- **용도**: 최적의 근무 스케줄을 생성합니다.

### 1.6 `BinaryProtocolHandler`

- **목적**: C++ 클라이언트를 위한 바이너리 프로토콜(8바이트 헤더 + JSON 데이터)을 처리합니다.
- **주요 메서드**:
  - `create_endian_error_response() -> Dict[str, Any]`: 엔디언 불일치 오류 응답을 생성합니다.
  - `recv_exact(conn: socket.socket, n: int) -> bytes`: 지정된 바이트 수만큼 데이터를 정확히 수신합니다.
  - `receive_packet(conn: socket.socket) -> Tuple[Optional[Dict[str, Any]], Optional[bytes]]`: 바이너리 패킷을 수신하고 JSON 데이터를 파싱합니다.
  - `send_json_response(conn: socket.socket, json_str: str)`: JSON 응답을 바이너리 프로토콜 형식으로 전송합니다.
- **용도**: little-endian 형식의 바이너리 데이터를 처리하여 C++ 클라이언트와 호환됩니다.

### 1.7 `LegacyProtocolHandler`

- **목적**: Python 클라이언트를 위한 레거시 JSON 프로토콜(헤더 없이 JSON만 전송)을 처리합니다.
- **주요 메서드**:
  - `receive_json(conn: socket.socket) -> Optional[Dict[str, Any]]`: JSON 데이터를 수신하고 파싱합니다.
  - `send_json_response(conn: socket.socket, json_str: str)`: JSON 응답을 전송합니다.
- **용도**: 간단한 JSON 기반 통신을 지원합니다.

### 1.8 `ShiftSchedulerServer`

- **목적**: 서버의 전체 동작을 관리하며, 클라이언트 요청을 수신하고 처리합니다.
- **주요 메서드**:
  - `detect_protocol_type(conn: socket.socket) -> str`: 바이너리 또는 레거시 프로토콜을 감지합니다.
  - `_is_handover_request(request_data: Dict[str, Any]) -> bool`: 요청이 인수인계 요약인지 확인합니다.
  - `_is_schedule_request(request_data: Dict[str, Any]) -> bool`: 요청이 근무표 생성인지 확인합니다.
  - `_process_handover_request(request_data: Dict[str, Any]) -> Dict[str, Any]`: 인수인계 요약 요청을 처리합니다.
  - `_process_schedule_request(request_data: Dict[str, Any]) -> Dict[str, Any]`: 근무표 생성 요청을 처리합니다.
  - `_process_request(request_data: Dict[str, Any]) -> Dict[str, Any]`: 요청 유형에 따라 적절한 처리 함수로 라우팅합니다.
  - `_parse_target_month(target_month: Optional[str]) -> Tuple[datetime, int]`: 대상 월을 파싱하여 시작 날짜와 일수를 반환합니다.
  - `_format_schedule_response(schedule: List[Dict], start_date: datetime) -> List[Dict]`: 스케줄 데이터를 날짜 형식으로 포맷합니다.
  - `_handle_client(conn: socket.socket, addr: tuple)`: 클라이언트 연결을 처리합니다.
  - `start()`: 서버를 시작하고 클라이언트 연결을 대기합니다.
- **용도**: 요청 수신, 처리, 응답 및 프로토콜 감지, 오류 처리를 통합 관리합니다.

---

## 2. 주요 함수

### 2.1 `summarize_handover(input_text: str) -> Dict[str, Any]`

- **목적**: OpenAI API를 사용하여 인수인계 텍스트를 요약합니다.
- **입력**:
  - `input_text: str`: 요약할 인수인계 텍스트.
- **출력**: 성공 시 요약된 텍스트가 포함된 딕셔너리, 실패 시 오류 메시지가 포함된 딕셔너리.
- **주요 로직**:
  - OpenAI API 키가 없거나 입력 텍스트가 비어 있으면 오류를 반환합니다.
  - `gpt-3.5-turbo` 모델을 사용하여 텍스트를 요약합니다.
  - 처리 시간과 결과 길이를 로깅합니다.
- **용도**: 긴 인수인계 내용을 간결하게 요약하여 실무에 활용 가능하도록 합니다.

### 2.2 `RequestValidator.validate_staff_data(staff_data: Dict[str, Any]) -> List[Staff]`

- **목적**: 입력된 직원 데이터를 검증하고 `Staff` 객체 리스트로 변환합니다.
- **입력**:
  - `staff_data: Dict[str, Any]`: 직원 정보가 포함된 딕셔너리.
- **출력**: 검증된 `Staff` 객체 리스트.
- **주요 로직**:
  - `staff_id`, `name`, `grade`, `total_hours` 등 필수 필드를 확인하고 유효성을 검사합니다.
  - 누락된 필드나 잘못된 형식에 대해 `ShiftSchedulerError`를 발생시킵니다.
- **용도**: 스케줄링에 필요한 직원 데이터를 안전하게 준비합니다.

### 2.3 `RequestValidator.validate_shift_rules(custom_rules: Dict[str, Any], position_rules: PositionRules) -> ShiftRules`

- **목적**: 사용자 정의 근무 규칙을 검증하고 `ShiftRules` 객체로 변환합니다.
- **입력**:
  - `custom_rules: Dict[str, Any]`: 사용자 정의 근무 규칙.
  - `position_rules: PositionRules`: 직책별 기본 규칙.
- **출력**: 검증된 `ShiftRules` 객체.
- **주요 로직**:
  - 사용자 정의 규칙이 없으면 기본 규칙을 사용합니다.
  - 야간 근무와 휴무를 자동 감지하거나 기본값을 적용합니다.
- **용도**: 스케줄러가 사용할 근무 규칙을 준비합니다.

### 2.4 `RequestValidator._detect_shifts(shifts: List[str], position_rules: PositionRules) -> Tuple[List[str], List[str]]`

- **목적**: 근무 유형에서 야간 근무와 휴무를 자동으로 감지합니다.
- **입력**:
  - `shifts: List[str]`: 근무 유형 리스트.
  - `position_rules: PositionRules`: 직책별 규칙.
- **출력**: 야간 근무와 휴무 리스트의 튜플.
- **주요 로직**:
  - 키워드(예: 'night', 'off')와 약어(예: 'N', 'O')를 사용하여 근무 유형을 분류합니다.
  - 감지된 결과가 없으면 기본값을 사용합니다.
- **용도**: 명시적 정의가 없는 경우 근무 유형을 추론합니다.

### 2.5 `main()`

- **목적**: 서버의 진입점으로, `ShiftSchedulerServer`를 초기화하고 실행합니다.
- **주요 로직**:
  - 서버를 시작하고 예외를 처리하며, 종료 시 소켓을 닫습니다.
- **용도**: 서버를 실행하는 최상위 함수입니다.

---

## 3. 요약

- **`Staff`와 `ShiftRules`**: 데이터 구조를 정의하고 입력 데이터의 유효성을 보장합니다.
- **`PositionRules`**: 간호 및 소방 직원의 특수 제약 조건을 처리합니다.
- **`ShiftScheduler`**: OR-Tools를 활용하여 최적의 근무 스케줄을 생성합니다.
- **`ResponseLogger`**: 응답을 파일로 기록하여 추적성을 높입니다.
- **`BinaryProtocolHandler`와 `LegacyProtocolHandler`**: C++와 Python 클라이언트를 지원하며, 엔디언 문제를 처리합니다.
- **`ShiftSchedulerServer`**: 요청 수신, 처리, 응답 및 프로토콜 감지를 통합 관리합니다.
- **`summarize_handover`**: OpenAI API로 인수인계 텍스트를 요약합니다.

이 코드는 복잡한 근무 스케줄링 문제를 해결하면서 다양한 클라이언트와의 호환성과 오류 처리를 강화한 견고한 서버 구현입니다. 추가 질문이 있으시면 언제든 말씀해주세요!