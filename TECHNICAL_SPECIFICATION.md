# Shift Scheduler Server - 기술명세서

## 📋 개요

**Optimized Shift Scheduler Server**는 OR-Tools CP-SAT 솔버를 활용한 간호/소방 직군 근무표 자동 생성 서버와 OpenAI 기반 인수인계 요약 기능을 통합한 TCP 서버입니다.

### 주요 특징
- 🏥 **직군별 특화 제약조건** (간호, 소방, 기본)
- ⚡ **고성능 최적화** 솔버 (OR-Tools CP-SAT)
- 🤖 **AI 인수인계 요약** (OpenAI GPT-3.5-turbo)
- 🌐 **다중 프로토콜 지원** (C++/Python 클라이언트 호환)
- 🔒 **안전한 한글 인코딩** 처리
- 📊 **상세 로깅 및 디버깅**

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                    TCP Server (Port 6004)                      │
├─────────────────────────────────────────────────────────────────┤
│  Request Router                                                 │
│  ┌─────────────────┐  ┌─────────────────────────────────────┐   │
│  │ Task Requests   │  │ Schedule Generation                 │   │
│  │ - handover      │  │ - Staff validation                  │   │
│  │ - summarization │  │ - Constraint application            │   │
│  └─────────────────┘  │ - OR-Tools CP-SAT solving           │   │
│           │           │ - Result formatting                 │   │
│           ▼           └─────────────────────────────────────┘   │
│  ┌─────────────────┐                                            │
│  │ OpenAI          │                                            │
│  │ Integration     │                                            │
│  │ (Optional)      │                                            │
│  └─────────────────┘                                            │
├─────────────────────────────────────────────────────────────────┤
│  Core Libraries                                                 │
│  • OR-Tools CP-SAT  • OpenAI API  • Python-dotenv             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 주요 기능

### 1. 근무표 자동 생성
- **직군별 제약조건 적용**: 간호(신규간호사 야간금지), 소방(24시간 당직 순환)
- **유연한 시프트 설정**: 명시적 지정 또는 자동 감지
- **월간 근무시간 관리**: 개인별 상한선 적용
- **최적화 알고리즘**: CP-SAT 솔버로 30초 내 해결

### 2. AI 인수인계 요약
- **자연어 처리**: GPT-3.5-turbo 모델 활용
- **한국어 최적화**: 의료/간호 전문 용어 이해
- **핵심 추출**: 중요도 기반 정보 압축
- **실시간 처리**: 평균 2-3초 응답

### 3. 다중 프로토콜 지원
- **C++ 클라이언트**: `py_gen_timetable` 프로토콜
- **Python 클라이언트**: 직접 JSON 통신
- **Task 기반 라우팅**: 기능별 요청 분기

---

## 📡 API 명세

### 근무표 생성 API

#### 요청 형식 (C++ 클라이언트)
```json
{
  "protocol": "py_gen_timetable",
  "data": {
    "staff_data": {
      "staff": [
        {
          "name": "홍길동",
          "staff_id": 1,
          "grade": 3,
          "total_monthly_work_hours": 180,
          "position": "간호"
        }
      ]
    },
    "position": "간호",
    "target_month": "2025-09",
    "custom_rules": {
      "shifts": ["Day", "Evening", "Night", "Off"],
      "shift_hours": {"Day": 8, "Evening": 8, "Night": 8, "Off": 0},
      "night_shifts": ["Night"],
      "off_shifts": ["Off"]
    }
  }
}
```

#### 응답 형식
```json
{
  "protocol": "py_gen_schedule",
  "resp": "success",
  "data": [
    {
      "date": "2025-09-01",
      "shift": "Day",
      "hours": 8,
      "people": [
        {
          "name": "홍길동",
          "staff_id": 1,
          "grade": 3
        }
      ]
    }
  ]
}
```

### 인수인계 요약 API

#### 요청 형식
```json
{
  "task": "summarize_handover",
  "input_text": "오늘 인수인계 내용은 다음과 같습니다: 1. 간병실 501호..."
}
```

#### 응답 형식
```json
{
  "status": "success",
  "task": "summarize_handover",
  "result": "핵심 요약 내용:\n1. 간병실 501호 - 혈압 불안정, 2시간마다 체크\n2. ..."
}
```

---

## 📊 데이터 구조

### Staff 객체
```python
@dataclass
class Staff:
    name: str             # 직원명
    staff_id: int         # 직원 ID
    grade: int            # 직급/등급
    total_hours: int      # 월 근무시간 상한
    position: str         # 직군 ("간호", "소방", "default")
    grade_name: str       # 직급명 (선택사항)
```

### ShiftRules 객체
```python
@dataclass
class ShiftRules:
    shifts: List[str]           # 전체 시프트 목록
    shift_hours: Dict[str, int] # 시프트별 근무시간
    night_shifts: List[str]     # 야간 시프트 목록
    off_shifts: List[str]       # 휴무 시프트 목록
```

### PositionRules 설정
```python
POSITION_RULES = {
    "간호": {
        "newbie_no_night": True,    # 신규간호사 야간금지
        "night_after_off": True,    # 야간 후 휴무
        "max_monthly_hours": 209,   # 월 최대시간
        "newbie_grade": 5           # 신규간호사 등급
    },
    "소방": {
        "night_after_off": True,    # 당직 후 휴무
        "max_monthly_hours": 190    # 월 최대시간
    }
}
```

---

## 🛠️ 설치 및 실행

### 1. 환경 준비
```bash
# 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements_optimized.txt
```

### 2. 환경변수 설정
```bash
# .env 파일 생성
echo "OPENAI_API_KEY=your-actual-openai-api-key" > .env
```

### 3. 서버 실행
```bash
python3 shift_server_optimized.py
```

### 4. 실행 로그 예시
```
2025-08-08 08:51:45 [INFO] Starting Optimized Shift Scheduler Server
2025-08-08 08:51:45 [INFO] Shift scheduler server started on 127.0.0.1:6004
```

---

## ⚙️ 설정 가이드

### 기본 설정
```python
# 서버 설정
HOST = '127.0.0.1'              # 바인딩 주소
PORT = 6004                     # 서버 포트
SOLVER_TIMEOUT_SECONDS = 30.0   # 솔버 제한시간

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
```

### OpenAI 설정
```python
# 자동 감지 및 초기화
if OPENAI_AVAILABLE:
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
```

### 직군별 제약조건 커스터마이징
```python
# POSITION_RULES 딕셔너리 수정
POSITION_RULES["새직군"] = PositionRules(
    newbie_no_night=False,
    night_after_off=True,
    max_monthly_hours=200,
    default_shifts=['A', 'B', 'C', 'Off'],
    default_shift_hours={'A': 12, 'B': 12, 'C': 8, 'Off': 0}
)
```

---

## 🔍 테스트 및 검증

### 기능별 테스트 스크립트

1. **근무표 생성 테스트**
```bash
python3 test_optimized_server.py
```

2. **인수인계 요약 테스트**
```bash
python3 test_handover_optimized.py
```

3. **다양한 시나리오 테스트**
```bash
python3 test_recommended.py     # 권장 시나리오
python3 test_error_scenarios.py # 오류 시나리오
```

### 성능 벤치마크
- **근무표 생성**: 평균 3-5초 (30명 기준)
- **인수인계 요약**: 평균 2-3초 (OpenAI API 속도 의존)
- **동시 연결**: 최대 5개 클라이언트
- **메모리 사용량**: 약 50-100MB

---

## 🚨 오류 처리

### 1. 입력 검증 오류
```json
{
  "protocol": "py_gen_schedule",
  "resp": "fail",
  "data": [],
  "error": "staff_data.staff 필드가 없거나 비어있음"
}
```

### 2. 솔버 실패
```json
{
  "protocol": "py_gen_schedule",
  "resp": "fail", 
  "data": [],
  "reason": "제약조건 충돌로 해를 찾을 수 없습니다"
}
```

### 3. OpenAI API 오류
```json
{
  "status": "error",
  "task": "summarize_handover",
  "reason": "OpenAI API 키가 설정되지 않았습니다"
}
```

### 4. 일반적인 오류 대응
- **포트 충돌**: `PORT = 6005` 등으로 변경
- **메모리 부족**: 직원 수 또는 시프트 복잡도 줄이기
- **네트워크 오류**: 방화벽 및 네트워크 설정 확인
- **인코딩 오류**: UTF-8, CP949, Latin-1 순으로 자동 시도

---

## ⚠️ 프로토콜 호환성 및 주의사항

### 바이너리 프로토콜 엔디언 설정

#### 🔴 **CRITICAL: Little-Endian 필수 사용**

**C++ 클라이언트와의 호환성을 위해 반드시 Little-endian 사용**

```python
# ✅ 올바른 구현 (Little-endian)
PROTOCOL_HEADER_FORMAT = '<II'  # Little-endian uint32_t × 2
header = struct.pack('<II', total_size, json_size)

# ❌ 절대 사용 금지 (Big-endian)
header = struct.pack('>II', total_size, json_size)  # C++ 클라이언트 통신 불가!
```

#### 🕵️ **과거 발생했던 실제 문제 사례**

**증상**: `"[Python 통신] 응답 수신 실패"` 오류
```
C++ 클라이언트 로그:
[ERROR] 헤더 정보 비정상: jsonSize=1919951483, totalSize=1668248687
```

**원인**: Big-endian (`'>II'`) 사용으로 인한 바이트 순서 불일치
- Python 서버: 125바이트 → Big-endian `[0x00,0x00,0x00,0x7D]`
- C++ 클라이언트: Little-endian 해석 → `0x7D000000` (2GB)

**해결**: Little-endian (`'<II'`) 변경으로 완전 해결

#### 📋 **아키텍처별 엔디언 특성**

| 아키텍처 | 엔디언 | 시장 점유율 | 비고 |
|----------|--------|-------------|------|
| x86-64 | Little | 90%+ (서버) | Intel/AMD PC |
| ARM64 | Little | 95%+ (모바일) | Apple Silicon, 스마트폰 |
| PowerPC | Big | <1% | 구형 시스템 |

**결론**: 현재 시스템 대부분이 Little-endian이므로 `'<II'` 사용이 표준

#### 🛡️ **안전한 프로토콜 설계 원칙**

```python
# 1. 상수로 명시적 정의
BINARY_PROTOCOL_ENDIAN = '<'  # Little-endian for C++ compatibility
HEADER_STRUCT = struct.Struct(BINARY_PROTOCOL_ENDIAN + 'II')

def pack_header(total_size: int, json_size: int) -> bytes:
    """
    Pack binary header for C++ client compatibility.
    
    IMPORTANT: Uses little-endian to match x86-64 uint32_t layout.
    DO NOT change to big-endian - will break C++ communication.
    
    Args:
        total_size: Total packet size in bytes
        json_size: JSON data size in bytes
        
    Returns:
        8-byte binary header (little-endian)
    """
    return HEADER_STRUCT.pack(total_size, json_size)
```

#### 🔧 **개발/운영 체크리스트**

**개발 시 필수 확인사항:**
- [ ] `struct.pack` 사용 시 항상 `'<II'` (Little-endian) 사용
- [ ] C++ 클라이언트와 실제 통합 테스트 수행
- [ ] 바이트 레벨 헤더 검증 테스트 작성
- [ ] 크로스 플랫폼 호환성 확인

**코드 리뷰 시 점검사항:**
- [ ] 엔디언 설정 변경 여부 확인 (`'<'` → `'>'` 변경 금지)
- [ ] struct.pack 포맷 문자열 검토
- [ ] 네트워크 바이트 순서 개념 혼동 확인
- [ ] 테스트 커버리지에 C++ 클라이언트 포함 여부

**운영 모니터링:**
- [ ] C++ 클라이언트 통신 실패율 추적
- [ ] "헤더 정보 비정상" 오류 알림 설정
- [ ] 바이트 순서 관련 오류 패턴 감지

---

## 📈 제약사항 및 권장사항

### 제약사항
- **최대 직원 수**: 100명 (성능상 권장)
- **최대 시프트 종류**: 10개
- **솔버 제한시간**: 30초
- **OpenAI 요청 제한**: API 사용량에 따라 제한
- **동시 연결**: 5개 클라이언트

### 권장사항
- **직원 수**: 3-50명 (최적 성능)
- **시프트 개수**: 3-6개 (간단할수록 빠름)
- **월 근무시간**: 개인당 150-250시간
- **가상환경 사용**: 의존성 충돌 방지
- **로그 모니터링**: 성능 및 오류 추적

---

## 🔒 보안 고려사항

### API 키 보안
- `.env` 파일을 `.gitignore`에 추가
- 환경변수로 API 키 관리
- 프로덕션에서는 시크릿 관리 도구 사용

### 네트워크 보안
- 내부 네트워크에서만 서버 실행 권장
- 필요시 SSL/TLS 래퍼 추가
- 입력 검증으로 인젝션 공격 방지

### 데이터 보안
- 개인정보 로깅 최소화
- 요청/응답 데이터 암호화 (필요시)
- 정기적인 로그 정리

---

## 🔄 확장성 및 유지보수

### 새로운 직군 추가
1. `POSITION_RULES`에 새 직군 규칙 추가
2. 필요시 `apply_constraints()` 함수에 특화 로직 추가
3. 테스트 케이스 작성

### 새로운 AI 기능 추가
1. `_process_request()`에 새 task 라우팅 추가
2. 해당 기능 함수 구현
3. 테스트 클라이언트 작성

### 성능 최적화
- 솔버 파라미터 튜닝
- 제약조건 간소화
- 캐싱 메커니즘 도입
- 비동기 처리 (asyncio) 전환

---

## 📝 버전 히스토리

### v2.0 (Current)
- OpenAI 인수인계 요약 기능 추가
- Task 기반 라우팅 시스템
- 환경변수 기반 설정 관리
- 향상된 오류 처리

### v1.0
- OR-Tools CP-SAT 솔버 통합
- 간호/소방 직군 특화 제약조건
- TCP 서버 기본 구조
- 한글 인코딩 처리

---

## 📞 문의 및 지원

### 개발팀 연락처
- **기술 문의**: 개발팀 이메일
- **버그 리포트**: GitHub Issues
- **기능 요청**: 제품 관리팀

### 참고 자료
- [OR-Tools 공식 문서](https://developers.google.com/optimization)
- [OpenAI API 가이드](https://platform.openai.com/docs)
- [Python TCP 소켓 프로그래밍](https://docs.python.org/3/library/socket.html)

---

*본 문서는 Shift Scheduler Server v2.0 기준으로 작성되었습니다.*
*최종 업데이트: 2025-08-08*