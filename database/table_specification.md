# 📋 데이터베이스 테이블 설명서

> 개선된 근무표 관리 시스템 데이터베이스 상세 명세서

---

## 📚 목차
1. [Core Tables](#core-tables) - 핵심 업무 테이블
2. [Configuration Tables](#configuration-tables) - 설정 및 참조 테이블  
3. [History & Audit Tables](#history--audit-tables) - 이력 및 감사 테이블
4. [Index Strategy](#index-strategy) - 인덱스 전략
5. [Business Rules](#business-rules) - 비즈니스 규칙

---

## Core Tables

### 🏢 `team` - 팀/부서 정보
**목적**: 병원 내 각 병동/부서의 기본 정보 관리

| 컬럼명 | 데이터타입 | 제약조건 | 설명 | 예시값 |
|--------|------------|----------|------|--------|
| `team_id` | INTEGER | PK, AUTO_INCREMENT | 팀 고유 식별자 | 1, 2, 3 |
| `team_name` | VARCHAR(100) | NOT NULL | 팀명 | "응급실", "내과병동" |
| `team_code` | VARCHAR(10) | UNIQUE | 팀 코드 | "ER", "IM" |
| `shift_type` | TINYINT | DEFAULT 3 | 교대제 유형 | 2(2교대), 3(3교대), 4(4교대) |
| `max_members` | TINYINT | DEFAULT 20 | 최대 인원수 | 15, 20, 25 |
| `is_active` | BOOLEAN | DEFAULT TRUE | 활성 상태 | TRUE, FALSE |
| `created_at` | TIMESTAMP | DEFAULT NOW() | 생성 시간 | 2025-08-02 10:30:00 |
| `updated_at` | TIMESTAMP | ON UPDATE NOW() | 수정 시간 | 2025-08-02 15:45:00 |

**비즈니스 규칙**:
- 팀 코드는 대문자로 통일
- shift_type에 따라 근무 시간대 조합이 결정됨
- 비활성 팀은 새로운 스케줄 생성 불가

**인덱스**:
- `PRIMARY KEY (team_id)`
- `UNIQUE KEY uk_team_code (team_code)`
- `KEY idx_active (is_active)`

---

### 👤 `staff` - 직원 기본 정보  
**목적**: 병원 직원의 기본 정보 및 팀 소속 관리

| 컬럼명 | 데이터타입 | 제약조건 | 설명 | 예시값 |
|--------|------------|----------|------|--------|
| `staff_id` | VARCHAR(255) | PK | 직원 고유 식별자 | "101", "EMP2025001" |
| `name` | VARCHAR(100) | NOT NULL | 직원 이름 | "김철수", "이영희" |
| `pw` | VARCHAR(255) | NULL | 비밀번호(해시) | bcrypt 해시값 |
| `position` | VARCHAR(100) | NULL | 직급/직책 | "간호사", "의사", "수련의" |
| `team_id` | INTEGER | NOT NULL, FK | 소속 팀 ID | 1, 2, 3 |
| `grade` | TINYINT | DEFAULT 1 | 등급 (1-5) | 1(신입), 3(중급), 5(전문가) |
| `grade_name` | VARCHAR(50) | NULL | 등급명 | "신입간호사", "수석간호사" |
| `is_active` | BOOLEAN | DEFAULT TRUE | 활성 상태 | TRUE, FALSE |
| `created_at` | TIMESTAMP | DEFAULT NOW() | 생성 시간 | 2025-08-02 09:00:00 |
| `updated_at` | TIMESTAMP | ON UPDATE NOW() | 수정 시간 | 2025-08-02 14:20:00 |

**비즈니스 규칙**:
- staff_id는 변경 불가 (근무표 이력 추적을 위해)
- 팀 이동 시에는 기존 스케줄 완료 후 변경
- grade는 근무표 생성 시 제약조건에 영향

**인덱스**:
- `PRIMARY KEY (staff_id)`
- `KEY idx_team (team_id)`
- `KEY idx_active_team (is_active, team_id)`

---

### 📅 `duty_schedule` - 근무 스케줄 (메인)
**목적**: 팀별 월간 근무표의 실제 근무 배정 정보

| 컬럼명 | 데이터타입 | 제약조건 | 설명 | 예시값 |
|--------|------------|----------|------|--------|
| `id` | BIGINT | PK, AUTO_INCREMENT | 스케줄 고유 식별자 | 1, 2, 3... |
| `staff_id` | VARCHAR(255) | NOT NULL, FK | 직원 ID | "101", "102" |
| `team_id` | INTEGER | NOT NULL, FK | 팀 ID | 1, 2, 3 |
| `schedule_month` | CHAR(7) | NOT NULL | 근무 월 | "2025-08", "2025-09" |
| `duty_date` | DATE | NOT NULL | 근무 날짜 | 2025-08-15 |
| `shift_code` | CHAR(1) | NOT NULL, FK | 근무 시간대 코드 | 'D', 'E', 'N', 'O' |
| `work_hours` | TINYINT | DEFAULT 8 | 근무 시간 | 8, 12, 0(휴무) |
| `is_changed` | BOOLEAN | DEFAULT FALSE | 변경 요청 적용 여부 | TRUE, FALSE |
| `change_reason` | VARCHAR(255) | NULL | 변경 사유 | "개인 사정", "병가" |
| `created_at` | TIMESTAMP | DEFAULT NOW() | 생성 시간 | 2025-08-02 08:00:00 |
| `updated_at` | TIMESTAMP | ON UPDATE NOW() | 수정 시간 | 2025-08-02 16:30:00 |

**비즈니스 규칙**:
- 한 직원은 하루에 하나의 근무만 배정 가능
- 'N'(야간) 근무 후 다음날은 반드시 'O'(휴무)
- 주간 근무시간 40시간 초과 불가
- 월 최소 휴무일 3일 보장

**인덱스**:
- `PRIMARY KEY (id)`
- `UNIQUE KEY uk_staff_date (staff_id, duty_date)`
- `KEY idx_team_month (team_id, schedule_month)`
- `KEY idx_staff_month (staff_id, schedule_month)`
- `KEY idx_date_range (duty_date)`

**파티셔닝**:
```sql
PARTITION BY RANGE (YEAR(duty_date) * 100 + MONTH(duty_date)) (
  PARTITION p202508 VALUES LESS THAN (202509),
  PARTITION p202509 VALUES LESS THAN (202510),
  -- 월별 파티션 자동 추가
);
```

---

## Configuration Tables

### ⏰ `shift_code` - 근무 시간대 정의
**목적**: 근무 시간대별 상세 정보 및 UI 표시 설정

| 컬럼명 | 데이터타입 | 제약조건 | 설명 | 예시값 |
|--------|------------|----------|------|--------|
| `shift_code` | CHAR(1) | PK | 시간대 코드 | 'D', 'E', 'N', 'O' |
| `shift_name` | VARCHAR(50) | NOT NULL | 시간대 명칭 | "Day", "Evening", "Night", "Off" |
| `start_time` | TIME | NULL | 시작 시간 | 08:00, 16:00, 00:00, NULL |
| `end_time` | TIME | NULL | 종료 시간 | 16:00, 00:00, 08:00, NULL |
| `work_hours` | TINYINT | DEFAULT 8 | 근무 시간 | 8, 8, 8, 0 |
| `description` | VARCHAR(255) | NULL | 설명 | "주간 근무", "야간 근무" |
| `color_code` | VARCHAR(7) | NULL | UI 색상 코드 | "#FFD700", "#4169E1" |
| `is_active` | BOOLEAN | DEFAULT TRUE | 활성 상태 | TRUE, FALSE |

**기본 데이터**:
```sql
INSERT INTO shift_code VALUES 
('D', 'Day', '08:00', '16:00', 8, '주간 근무', '#FFD700', TRUE),
('E', 'Evening', '16:00', '00:00', 8, '저녁 근무', '#FF8C00', TRUE),
('N', 'Night', '00:00', '08:00', 8, '야간 근무', '#4169E1', TRUE),
('O', 'Off', NULL, NULL, 0, '휴무', '#808080', TRUE);
```

---

### ⚙️ `team_constraint` - 팀별 제약조건
**목적**: 팀별 특수 제약조건 및 가중치 관리

| 컬럼명 | 데이터타입 | 제약조건 | 설명 | 예시값 |
|--------|------------|----------|------|--------|
| `id` | INTEGER | PK, AUTO_INCREMENT | 제약조건 고유 식별자 | 1, 2, 3 |
| `team_id` | INTEGER | NOT NULL, FK | 팀 ID | 1, 2, 3 |
| `constraint_type` | VARCHAR(100) | NOT NULL | 제약조건 유형 | "MIN_STAFF_PER_SHIFT" |
| `constraint_name` | VARCHAR(255) | NOT NULL | 제약조건 명칭 | "시간대별 최소 인원" |
| `params` | JSON | NULL | 제약조건 파라미터 | {"D": 3, "E": 2, "N": 2} |
| `weight_point` | TINYINT | DEFAULT 5 | 가중치 (1-10) | 8, 5, 3 |
| `is_active` | BOOLEAN | DEFAULT TRUE | 활성 상태 | TRUE, FALSE |
| `description` | TEXT | NULL | 상세 설명 | "응급실은 야간에 최소 2명 필요" |

**제약조건 유형 예시**:
- `MIN_STAFF_PER_SHIFT`: 시간대별 최소 인원
- `MAX_CONSECUTIVE_NIGHTS`: 연속 야간 근무 제한
- `GRADE_DISTRIBUTION`: 등급별 인원 분배
- `WEEKEND_COVERAGE`: 주말 커버리지 요구사항

---

### 🔗 `shift_constraint_rule` - 근무 시간대 연결 규칙
**목적**: 근무 시간대 간 허용/금지 규칙 정의

| 컬럼명 | 데이터타입 | 제약조건 | 설명 | 예시값 |
|--------|------------|----------|------|--------|
| `id` | INTEGER | PK, AUTO_INCREMENT | 규칙 고유 식별자 | 1, 2, 3 |
| `rule_name` | VARCHAR(100) | NOT NULL | 규칙 명칭 | "야간 후 휴무", "연속 야간 금지" |
| `shift_code_before` | CHAR(1) | FK | 이전 근무 코드 | 'N', 'D' |
| `shift_code_after` | CHAR(1) | FK | 다음 근무 코드 | 'O', 'N' |
| `constraint_type` | ENUM | DEFAULT 'FORBIDDEN' | 제약 유형 | 'FORBIDDEN', 'REQUIRED', 'PREFERRED' |
| `weight_point` | TINYINT | DEFAULT 5 | 가중치 | 10(강제), 5(권장), 1(선호) |
| `is_active` | BOOLEAN | DEFAULT TRUE | 활성 상태 | TRUE, FALSE |
| `description` | VARCHAR(255) | NULL | 규칙 설명 | "야간 근무 후 반드시 휴무" |

**기본 규칙 예시**:
```sql
INSERT INTO shift_constraint_rule VALUES 
(1, '야간 후 휴무', 'N', 'O', 'REQUIRED', 10, TRUE, '야간 근무 후 반드시 휴무'),
(2, '야간 후 저녁 금지', 'N', 'E', 'FORBIDDEN', 9, TRUE, '야간 근무 후 저녁 근무 금지'),
(3, '주간 후 야간 금지', 'D', 'N', 'FORBIDDEN', 7, TRUE, '주간 근무 후 바로 야간 근무 금지');
```

---

## History & Audit Tables

### 📊 `schedule_history` - 근무표 변경 이력
**목적**: 모든 근무표 변경사항 추적 및 감사

| 컬럼명 | 데이터타입 | 제약조건 | 설명 | 예시값 |
|--------|------------|----------|------|--------|
| `id` | BIGINT | PK, AUTO_INCREMENT | 이력 고유 식별자 | 1, 2, 3... |
| `staff_id` | VARCHAR(255) | NOT NULL, FK | 직원 ID | "101", "102" |
| `team_id` | INTEGER | NOT NULL, FK | 팀 ID | 1, 2 |
| `duty_date` | DATE | NOT NULL | 근무 날짜 | 2025-08-15 |
| `old_shift_code` | CHAR(1) | FK | 기존 근무 코드 | 'D', 'O' |
| `new_shift_code` | CHAR(1) | NOT NULL, FK | 변경된 근무 코드 | 'N', 'D' |
| `change_type` | ENUM | DEFAULT 'MANUAL' | 변경 유형 | 'MANUAL', 'AUTO', 'REQUEST' |
| `change_reason` | VARCHAR(255) | NULL | 변경 사유 | "직원 요청", "응급 상황" |
| `requested_by` | VARCHAR(255) | NULL | 요청자 | "101", "ADMIN" |
| `approved_by` | VARCHAR(255) | NULL | 승인자 | "MANAGER01" |
| `created_at` | TIMESTAMP | DEFAULT NOW() | 생성 시간 | 2025-08-02 14:30:00 |

**변경 유형**:
- `MANUAL`: 관리자 직접 수정
- `AUTO`: 시스템 자동 조정  
- `REQUEST`: 직원 요청 승인

---

### 📝 `change_requests` - 근무 변경 요청
**목적**: 직원의 근무 변경 요청 관리 및 승인 프로세스

| 컬럼명 | 데이터타입 | 제약조건 | 설명 | 예시값 |
|--------|------------|----------|------|--------|
| `id` | BIGINT | PK, AUTO_INCREMENT | 요청 고유 식별자 | 1, 2, 3... |
| `staff_id` | VARCHAR(255) | NOT NULL, FK | 요청자 직원 ID | "101", "102" |
| `team_id` | INTEGER | NOT NULL, FK | 팀 ID | 1, 2 |
| `duty_date` | DATE | NOT NULL | 변경 희망 날짜 | 2025-08-20 |
| `original_shift` | CHAR(1) | NOT NULL, FK | 기존 근무 코드 | 'D', 'N' |
| `desired_shift` | CHAR(1) | NOT NULL, FK | 희망 근무 코드 | 'O', 'D' |
| `request_reason` | VARCHAR(500) | NULL | 요청 사유 | "가족 행사 참석" |
| `status` | ENUM | DEFAULT 'PENDING' | 처리 상태 | 'PENDING', 'APPROVED', 'REJECTED', 'APPLIED' |
| `response_message` | TEXT | NULL | 처리 결과 메시지 | "승인되었습니다", "대체 인력 부족" |
| `processed_by` | VARCHAR(255) | NULL | 처리자 | "MANAGER01" |
| `processed_at` | TIMESTAMP | NULL | 처리 시간 | 2025-08-02 16:00:00 |
| `created_at` | TIMESTAMP | DEFAULT NOW() | 생성 시간 | 2025-08-02 10:00:00 |
| `updated_at` | TIMESTAMP | ON UPDATE NOW() | 수정 시간 | 2025-08-02 16:00:00 |

**처리 상태 흐름**:
1. `PENDING`: 요청 대기
2. `APPROVED`: 승인 (스케줄러 처리 대기)
3. `APPLIED`: 근무표 반영 완료
4. `REJECTED`: 거부

---

## Index Strategy

### 🎯 핵심 성능 인덱스

#### duty_schedule (메인 테이블)
```sql
-- 필수 인덱스
CREATE UNIQUE INDEX uk_staff_date ON duty_schedule(staff_id, duty_date);
CREATE INDEX idx_team_month ON duty_schedule(team_id, schedule_month);
CREATE INDEX idx_staff_month ON duty_schedule(staff_id, schedule_month);

-- 조회 최적화 인덱스  
CREATE INDEX idx_date_range ON duty_schedule(duty_date);
CREATE INDEX idx_shift_date ON duty_schedule(shift_code, duty_date);

-- 커버링 인덱스 (SELECT 성능 향상)
CREATE INDEX idx_team_date_shift ON duty_schedule(team_id, duty_date, shift_code);
```

#### 관계 테이블 인덱스
```sql
-- staff 테이블
CREATE INDEX idx_team_active ON staff(team_id, is_active);
CREATE INDEX idx_name ON staff(name); -- 검색용

-- change_requests 테이블  
CREATE INDEX idx_staff_status ON change_requests(staff_id, status);
CREATE INDEX idx_team_pending ON change_requests(team_id, status, created_at);

-- team_constraint 테이블
CREATE INDEX idx_team_type ON team_constraint(team_id, constraint_type, is_active);
```

### 📊 인덱스 사용률 모니터링
```sql
-- 인덱스 사용 통계 확인
SELECT 
    table_name,
    index_name,
    cardinality,
    non_unique
FROM information_schema.statistics 
WHERE table_schema = 'shifter' 
ORDER BY table_name, seq_in_index;
```

---

## Business Rules

### 🏥 병원 근무표 비즈니스 규칙

#### 1. 기본 근무 규칙
- **근무시간 제한**: 주 40시간 초과 불가
- **최소 휴무**: 월 3일 이상 휴무 보장
- **야간 후 휴무**: 야간 근무('N') 후 반드시 휴무('O')
- **연속 근무 제한**: 동일 시간대 3일 연속 금지

#### 2. 팀별 특수 규칙
- **최소 인력**: 각 시간대별 최소 인원 보장
- **등급 분배**: 신입/숙련자 적절 배치
- **응급상황 대응**: 야간/주말 전문 인력 배치

#### 3. 변경 요청 규칙
- **신청 마감**: 해당 월 15일까지 변경 요청 가능
- **승인 기준**: 대체 인력 확보 시에만 승인
- **응급 변경**: 병가/응급상황 시 즉시 처리

#### 4. 데이터 무결성 규칙
- **중복 방지**: 동일 직원-날짜 중복 배정 불가
- **팀 일관성**: 직원은 소속 팀 스케줄에만 배정
- **시간대 유효성**: 활성화된 shift_code만 사용

### 🔒 보안 및 권한 규칙
- **개인정보 보호**: 타팀 스케줄 조회 제한
- **변경 권한**: 팀장/관리자만 스케줄 수정 가능
- **감사 로그**: 모든 변경사항 이력 보존 (3년)

---

## 📈 성능 최적화 가이드

### 쿼리 최적화 팁
1. **팀별 조회시**: `team_id + schedule_month` 인덱스 활용
2. **개인 조회시**: `staff_id + duty_date` 복합 인덱스 활용  
3. **기간 조회시**: 파티션 프루닝 효과 활용
4. **집계 쿼리**: 커버링 인덱스로 디스크 I/O 최소화

### 배치 작업 최적화
1. **스케줄 생성**: 팀별 트랜잭션으로 분할
2. **이력 정리**: 월별 파티션 단위 아카이빙
3. **통계 수집**: 야간 배치로 인덱스 통계 갱신

이 문서는 개발팀과 DBA가 함께 참조할 수 있도록 작성되었습니다. 추가 질문이나 수정사항이 있으면 언제든 문의해 주세요! 🚀