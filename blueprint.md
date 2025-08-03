# Shifter 시스템 개선 청사진

## 1. 현재 시스템 분석

### 1.1 main.cpp 현황
- **역할**: TCP 서버 (포트 5556)로 클라이언트 요청 처리
- **주요 기능**:
  - Hello/Insert/GetSchedule/ChangeShift 프로토콜 처리
  - MySQL DB 연결 및 스케줄 데이터 관리
  - Python 스크립트 실행 및 결과 처리
- **문제점**: 
  - 변경 요청 처리 로직 혼재
  - DB 갱신이 매번 전체 삭제/삽입으로 비효율적
  - 클라이언트 응답 처리 부족

### 1.2 shift_scheduler.py 현황
- **역할**: OR-Tools를 사용한 근무표 최적화 생성
- **주요 기능**:
  - 2/3/4교대 시스템 지원
  - 제약조건 기반 스케줄링 (주 40시간, 야간근무 후 휴무 등)
  - 변경 요청 JSON 파일 처리
- **문제점**:
  - 로그 메시지가 혼란스러움 (변경 방향 반대 기록)
  - 하드코딩된 직원 데이터

### 1.3 UI 요구사항 (PNG 분석)
- **로그인 시스템**: 이메일/패스워드 기반
- **관리자 대시보드**: 직원관리, 근무표생성, 근무표관리, 근무기록
- **직원 관리**: 회사정보, 직급정보, 직원정보 등록
- **근무표 관리**: 생성, 수정, 확인, 변경요청 승인/반려
- **근무기록**: 출퇴근 확인, 통계 제공

## 2. 개선 계획

### 2.1 main.cpp 개선사항

#### 2.1.1 프로토콜 체계 정리
```cpp
// 새로운 프로토콜 정의
- "login": 로그인 처리
- "ReqTodaysDuty": 오늘의 근무정보 조회
- "GetStaffList": 직원 목록 조회
- "RegisterStaff": 직원 등록
- "CreateSchedule": 근무표 생성
- "ModifySchedule": 근무표 수정
- "ApproveChangeRequest": 변경요청 승인/반려
- "GetWorkRecord": 근무기록 조회
```

#### 2.1.2 DB 효율성 개선
```cpp
// 기존 문제
- 매번 전체 삭제/삽입 → 비효율적
- 트랜잭션 내에서 Python 실행 → 긴 대기시간

// 개선방안
void updateScheduleEfficiently(MYSQL* conn, const json& changes) {
    // 1. 변경사항만 업데이트
    // 2. 트랜잭션 분리
    // 3. 배치 처리
}
```

#### 2.1.3 응답 처리 개선
```cpp
// 현재: 클라이언트 연결이 갑자기 끊어짐
// 개선: 명확한 응답 구조
{
    "Protocol": "change_response",
    "success": true/false,
    "message": "변경 완료/실패 메시지",
    "data": { ... }
}
```

### 2.2 shift_scheduler.py 개선사항

#### 2.2.1 로그 메시지 정확성 개선
```python
# 현재 문제
print(f"[INFO] {sid}의 {req['date']} 근무를 {s}로 고정")
# → 변경 방향이 불분명

# 개선안
print(f"[INFO] {sid}의 {req['date']} 근무를 {original_s}에서 {s}로 변경 요청 적용")
```

#### 2.2.2 동적 직원 데이터 처리
```python
# 현재: 하드코딩된 staff_data
# 개선: JSON 파일 또는 DB에서 동적 로딩
def load_staff_data_from_db():
    # DB 연결 후 직원 데이터 로드
    pass
```

#### 2.2.3 변경 결과 명확한 피드백
```python
# 변경 성공/실패에 대한 명확한 상태 반환
if change_applied and status == cp_model.OPTIMAL:
    print("[SUCCESS] 변경 요청이 성공적으로 반영됨")
    return {"status": "success", "changes_applied": True}
elif not change_applied:
    print("[INFO] 변경 요청 없음")
    return {"status": "success", "changes_applied": False}
else:
    print("[ERROR] 변경 요청 처리 실패")
    return {"status": "error", "message": "제약조건 충돌"}
```

### 2.3 새로운 기능 구현

#### 2.3.1 로그인 시스템
```cpp
// main.cpp에 추가
else if (j.contains("Protocol") && j["Protocol"] == "login") {
    std::string id = j["data"]["id"];
    std::string pw = j["data"]["pw"];
    
    // DB에서 사용자 인증
    bool authenticated = authenticate_user(conn, id, pw);
    
    j["Protocol"] = authenticated ? "login_success" : "login_failed";
    sendWorkItem(clientSocket, WorkItem{j.dump(), {}});
}
```

#### 2.3.2 직원 관리 기능
```cpp
// 직원 등록
else if (j.contains("Protocol") && j["Protocol"] == "RegisterStaff") {
    auto staff_info = j["data"];
    bool result = register_staff_to_db(conn, staff_info);
    
    j["Protocol"] = result ? "register_success" : "register_failed";
    sendWorkItem(clientSocket, WorkItem{j.dump(), {}});
}
```

#### 2.3.3 오늘의 근무정보 조회
```cpp
else if (j.contains("Protocol") && j["Protocol"] == "ReqTodaysDuty") {
    std::string team_id = j["data"]["team_id"];
    std::string date = j["data"]["date"];
    
    json today_schedule = get_today_schedule(conn, team_id, date);
    
    j["Protocol"] = "TodaysDutyResponse";
    j["data"] = today_schedule;
    sendWorkItem(clientSocket, WorkItem{j.dump(), {}});
}
```

## 3. 데이터베이스 스키마 (database/ 참고)

### 3.1 개선된 테이블 구조 적용
**기반**: `/database/table_structure.md`의 8개 핵심 테이블

#### Core Tables
- **`team`**: 팀/부서 정보 (교대제 유형, 최대 인원 등)
- **`staff`**: 직원 기본 정보 (팀 소속, 등급, 활성 상태)
- **`duty_schedule`**: 근무 스케줄 메인 테이블 (월별 파티셔닝)

#### Configuration Tables  
- **`shift_code`**: 근무 시간대 정의 (D/E/N/O, 시간, 색상)
- **`team_constraint`**: 팀별 제약조건 (JSON 파라미터)
- **`shift_constraint_rule`**: 시간대 연결 규칙 (야간→휴무 등)

#### History & Audit Tables
- **`schedule_history`**: 근무표 변경 이력 추적
- **`change_requests`**: 근무 변경 요청 관리

### 3.2 성능 최적화 전략
**기반**: `/database/erd_diagram.md`의 인덱스 전략

```sql
-- 핵심 성능 인덱스
CREATE UNIQUE INDEX uk_staff_date ON duty_schedule(staff_id, duty_date);
CREATE INDEX idx_team_month ON duty_schedule(team_id, schedule_month);
CREATE INDEX idx_staff_month ON duty_schedule(staff_id, schedule_month);

-- 월별 파티셔닝
PARTITION BY RANGE (YEAR(duty_date) * 100 + MONTH(duty_date));
```

### 3.3 비즈니스 규칙 적용
**기반**: `/database/table_specification.md`의 병원 근무표 규칙

- 주 40시간 제한, 월 3일 이상 휴무
- 야간 근무 후 반드시 휴무
- 팀별 최소 인원 보장
- 등급별 적절 배치

## 4. 구현 우선순위

### Phase 1: 핵심 버그 수정 (1주)
1. **shift_scheduler.py 로그 메시지 수정**
   - 변경 방향 명확화: `A에서 B로 변경` 형태
   - 변경 결과 상태 반환 구조화
2. **DB 갱신 로직 개선**
   - 변경사항 없을 때 DB 갱신 스킵
   - 트랜잭션 범위 최적화
3. **클라이언트 응답 처리 완성**
   - JSON 응답 구조 표준화
   - 연결 종료 전 결과 전송 보장

### Phase 2: 프로토콜 확장 (2주)
1. **로그인 프로토콜 구현**
   - staff 테이블 기반 인증
   - 세션 관리 (선택사항)
2. **TodaysDuty 프로토콜 구현**
   - 팀별/날짜별 근무 현황 조회
   - duty_schedule 테이블 연동
3. **직원관리 프로토콜 구현**
   - CRUD 기본 기능
   - 팀 배정 및 등급 관리

### Phase 3: 고급 기능 (3주)
1. **변경요청 승인/반려 시스템**
   - change_requests 테이블 연동
   - 승인 워크플로우 구현
2. **근무표 생성/수정 기능**
   - Python 스케줄러 연동 개선
   - 제약조건 적용 (team_constraint)
3. **이력 추적 시스템**
   - schedule_history 자동 기록
   - 변경 감사 로그

### Phase 4: UI 연동 (2주)
1. **웹 클라이언트 구현**
   - PNG 설계 기반 UI 개발
   - 반응형 디자인 적용
2. **실시간 업데이트**
   - WebSocket 또는 폴링
   - 근무표 실시간 동기화

## 5. 예상 개선 효과

### 5.1 성능 개선
- **DB 조회**: 월별 파티셔닝으로 **20-50배 향상**
- **DB 갱신**: 부분 업데이트로 **90% 성능 향상**  
- **응답시간**: 불필요한 Python 실행 제거로 **50% 단축**

### 5.2 안정성 개선
- 명확한 에러 핸들링 및 로깅
- 트랜잭션 분리로 데드락 방지
- 클라이언트 응답 보장으로 연결 안정성 확보
- 데이터 무결성 제약조건 강화

### 5.3 사용성 개선
- 직관적인 웹 UI 제공
- 실시간 근무표 확인 및 변경요청
- 승인/반려 워크플로우로 체계적 관리
- 상세한 이력 추적으로 감사 기능 강화

## 6. 구현 시 주의사항

### 6.1 기술적 고려사항
1. **하위 호환성**: 기존 프로토콜과의 호환성 유지
2. **동시성**: race condition 방지를 위한 적절한 락 전략
3. **에러 처리**: 모든 예외 상황에 대한 적절한 응답
4. **데이터 타입**: database/ 스키마의 타입 정의 준수

### 6.2 보안 고려사항
1. **패스워드 보안**: bcrypt 해싱 적용
2. **SQL Injection**: 준비된 문(Prepared Statement) 사용
3. **권한 관리**: 팀별/역할별 접근 제어
4. **감사 로그**: 모든 중요 작업 이력 보존

### 6.3 데이터베이스 마이그레이션
1. **기존 데이터 보존**: 현재 데이터의 안전한 이관
2. **점진적 마이그레이션**: 서비스 중단 최소화
3. **백업 전략**: 마이그레이션 전 완전 백업
4. **롤백 계획**: 문제 발생 시 복구 방안

## 7. 검증 및 테스트 계획

### 7.1 단위 테스트
- 각 프로토콜별 기능 테스트
- DB CRUD 연산 테스트
- Python 스케줄러 로직 테스트

### 7.2 통합 테스트  
- 전체 워크플로우 테스트
- 다중 클라이언트 동시 접속 테스트
- 대용량 데이터 처리 성능 테스트

### 7.3 사용자 테스트
- 실제 병원 환경 시뮬레이션
- UI/UX 사용성 평가
- 업무 프로세스 적합성 검증

이 청사진을 바탕으로 단계별 구현을 진행하면 안정적이고 효율적인 근무표 관리 시스템을 구축할 수 있습니다. database/ 디렉터리의 상세 설계를 기반으로 하여 확장성과 성능을 동시에 확보한 시스템이 될 것입니다.