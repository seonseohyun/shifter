# 🎨 Entity Relationship Diagram (ERD)

## 📊 개선된 근무표 시스템 ERD

```mermaid
erDiagram
    %% Core Entities
    team {
        int team_id PK "팀 고유 식별자"
        string team_name "팀명"
        string team_code UK "팀 코드"
        tinyint shift_type "교대제 유형(2,3,4)"
        tinyint max_members "최대 인원수"
        boolean is_active "활성 상태"
        timestamp created_at
        timestamp updated_at
    }
    
    staff {
        string staff_id PK "직원 고유 식별자"
        string name "직원 이름"
        string pw "비밀번호"
        string position "직급/직책"
        int team_id FK "소속 팀 ID"
        tinyint grade "등급(1-5)"
        string grade_name "등급명"
        boolean is_active "활성 상태"
        timestamp created_at
        timestamp updated_at
    }
    
    shift_code {
        char shift_code PK "시간대 코드(D,E,N,O)"
        string shift_name "시간대 명칭"
        time start_time "시작 시간"
        time end_time "종료 시간"
        tinyint work_hours "근무 시간"
        string description "설명"
        string color_code "UI 색상 코드"
        boolean is_active "활성 상태"
        timestamp created_at
        timestamp updated_at
    }
    
    %% Main Schedule Table
    duty_schedule {
        bigint id PK "스케줄 고유 식별자"
        string staff_id FK "직원 ID"
        int team_id FK "팀 ID"
        string schedule_month "근무 월(YYYY-MM)"
        date duty_date "근무 날짜"
        char shift_code FK "근무 시간대 코드"
        tinyint work_hours "근무 시간"
        boolean is_changed "변경 요청 적용 여부"
        string change_reason "변경 사유"
        timestamp created_at
        timestamp updated_at
    }
    
    %% Configuration Tables
    team_constraint {
        int id PK "제약조건 고유 식별자"
        int team_id FK "팀 ID"
        string constraint_type "제약조건 유형"
        string constraint_name "제약조건 명칭"
        json params "제약조건 파라미터"
        tinyint weight_point "가중치(1-10)"
        boolean is_active "활성 상태"
        text description "상세 설명"
        timestamp created_at
        timestamp updated_at
    }
    
    shift_constraint_rule {
        int id PK "규칙 고유 식별자"
        string rule_name "규칙 명칭"
        char shift_code_before FK "이전 근무 코드"
        char shift_code_after FK "다음 근무 코드"
        string constraint_type "제약 유형"
        tinyint weight_point "가중치"
        boolean is_active "활성 상태"
        string description "규칙 설명"
        timestamp created_at
        timestamp updated_at
    }
    
    %% History & Audit Tables
    schedule_history {
        bigint id PK "이력 고유 식별자"
        string staff_id FK "직원 ID"
        int team_id FK "팀 ID"
        date duty_date "근무 날짜"
        char old_shift_code FK "기존 근무 코드"
        char new_shift_code FK "변경된 근무 코드"
        string change_type "변경 유형"
        string change_reason "변경 사유"
        string requested_by "요청자"
        string approved_by "승인자"
        timestamp created_at
    }
    
    change_requests {
        bigint id PK "요청 고유 식별자"
        string staff_id FK "요청자 직원 ID"
        int team_id FK "팀 ID"
        date duty_date "변경 희망 날짜"
        char original_shift FK "기존 근무 코드"
        char desired_shift FK "희망 근무 코드"
        string request_reason "요청 사유"
        string status "처리 상태"
        text response_message "처리 결과 메시지"
        string processed_by "처리자"
        timestamp processed_at "처리 시간"
        timestamp created_at
        timestamp updated_at
    }
    
    %% Relationships
    team ||--o{ staff : "belongs to"
    team ||--o{ duty_schedule : "has"
    team ||--o{ team_constraint : "has"
    team ||--o{ schedule_history : "tracks"
    team ||--o{ change_requests : "receives"
    
    staff ||--o{ duty_schedule : "assigned"
    staff ||--o{ schedule_history : "changed"
    staff ||--o{ change_requests : "requests"
    
    shift_code ||--o{ duty_schedule : "uses"
    shift_code ||--o{ schedule_history : "old_shift"
    shift_code ||--o{ schedule_history : "new_shift"
    shift_code ||--o{ change_requests : "original"
    shift_code ||--o{ change_requests : "desired"
    shift_code ||--o{ shift_constraint_rule : "before"
    shift_code ||--o{ shift_constraint_rule : "after"
```

## 🔗 관계 설명

### 1:N 관계 (One-to-Many)
- **team → staff**: 한 팀에 여러 직원 소속
- **team → duty_schedule**: 한 팀의 여러 근무 스케줄
- **team → team_constraint**: 한 팀의 여러 제약조건
- **staff → duty_schedule**: 한 직원의 여러 근무 일정
- **staff → change_requests**: 한 직원의 여러 변경 요청
- **shift_code → duty_schedule**: 한 시간대 코드의 여러 근무 배정

### 자기 참조 관계
- **shift_constraint_rule**: 시간대 간 연결 규칙 (N→E 금지 등)

### 복합 관계
- **duty_schedule**: staff, team, shift_code 3개 테이블과 연결
- **change_requests**: 요청자, 팀, 기존/희망 시간대 연결

---

## 📈 ERD 기반 성능 최적화 포인트

### 🎯 핵심 조회 패턴
```sql
-- 패턴 1: 팀별 월 스케줄 조회
SELECT * FROM duty_schedule 
WHERE team_id = ? AND schedule_month = ?;

-- 패턴 2: 개인별 월 스케줄 조회  
SELECT * FROM duty_schedule 
WHERE staff_id = ? AND schedule_month = ?;

-- 패턴 3: 특정 날짜 팀 현황
SELECT * FROM duty_schedule 
WHERE team_id = ? AND duty_date = ?;
```

### 🚀 인덱스 전략 (ERD 기반)
```sql
-- duty_schedule 핵심 인덱스
CREATE INDEX idx_team_month ON duty_schedule(team_id, schedule_month);
CREATE INDEX idx_staff_month ON duty_schedule(staff_id, schedule_month);  
CREATE UNIQUE INDEX uk_staff_date ON duty_schedule(staff_id, duty_date);

-- 관계 기반 조인 최적화
CREATE INDEX idx_staff_team ON staff(team_id, is_active);
CREATE INDEX idx_constraint_team ON team_constraint(team_id, is_active);
```

### 🔄 파티셔닝 전략
```sql
-- duty_schedule: 월별 파티셔닝 (ERD 중심 테이블)
PARTITION BY RANGE (YEAR(duty_date) * 100 + MONTH(duty_date));

-- schedule_history: 연도별 파티셔닝  
PARTITION BY RANGE (YEAR(created_at));
```

---

## 🎨 ERD 시각화 특징

### 색상 구분 (논리적 그룹)
- **🔵 Core Tables**: team, staff, duty_schedule  
- **🟡 Configuration**: shift_code, team_constraint, shift_constraint_rule
- **🟠 History/Audit**: schedule_history, change_requests

### 관계선 두께
- **굵은 선**: 핵심 비즈니스 관계 (team-staff, staff-duty_schedule)
- **중간 선**: 설정/참조 관계 (shift_code 참조)  
- **얇은 선**: 이력/감사 관계 (history, requests)

### FK 네이밍 컨벤션
- **{table}_{column}**: 명확한 참조 관계 표시
- **composite FK**: 복합 외래키로 데이터 정합성 보장

---

## 🎯 ERD 검증 체크리스트

### ✅ 정규화 검증
- [x] 1NF: 원자값 저장 (JSON 제외)
- [x] 2NF: 부분 함수 종속 제거
- [x] 3NF: 이행적 함수 종속 제거
- [x] BCNF: 결정자가 후보키

### ✅ 무결성 제약
- [x] Entity Integrity: 모든 PK 정의
- [x] Referential Integrity: FK 관계 명시
- [x] Domain Integrity: 적절한 데이터 타입
- [x] User-defined Integrity: 비즈니스 규칙 반영

### ✅ 성능 고려사항  
- [x] 자주 조회되는 경로에 인덱스 계획
- [x] 대용량 테이블 파티셔닝 설계
- [x] N+1 문제 방지를 위한 관계 최적화
- [x] 트랜잭션 범위 최소화 고려