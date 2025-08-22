# Shifter  
 - 교대근무 자동 스케줄링 & 근태/인계 관리 플랫폼

> **팀장/서버 담당:** @seonseohyun (선서현)  
> **클라이언트/관리자 프로그램 담당:** @XEB(김유범)  
> **클라이언트/이용자 프로그램 담당:** @turtle4105(유희라)    
> **파이썬 서버/알고리즘 및 AI 담당:** @sharpscar(박경태)  


> **Stack:** C++ TCP Server · Python Scheduler · MariaDB · WPF Client  
> **Domains:** 간호/소방/경찰 등 교대직군

---

##  프로젝트 한눈에 보기

본 프로젝트는 교대근무자의 과도한 업무와 법정 근로 규정 미준수로 인한 사회적 문제를 해결하기 위해 설계되었습니다.  
법정 근로 규제를 준수하며, 실제 근무 환경의 시나리오를 충실히 반영한 AI 기반 근무표 생성 시스템입니다.

---
## 목표

- 법적 제약조건(연속 야간근무 제한, 최소 휴식시간, 월 근무시간 상한) 준수
- 근무 변경 요청, 인수인계, 출퇴근 기록 등 실제 현장 업무 프로세스 구현
- 관리자/직원 모두 직관적으로 사용할 수 있는 클라이언트 제공
- 안정성과 확장성을 고려한 서버·DB 아키텍처 구축
---
## 개발환경

- Server: C++17, MariaDB Connector/C++, nlohmann-json
- Scheduler: Python 3.x, pandas, numpy
- DB: MariaDB 10.x
- Client: WPF (C#)
- OS: Windows 10
- IDE: Visual Studio 2022, PyCharm
---

## 주요 기능

- 근무표 자동 생성: 팀/직군 규칙과 개인 희망·제외 조건 반영
- 근무 변경 요청: 승인/반려, 사유 관리, 삭제 플래그 처리
- 인수인계 작성/조회: 교대·출장·휴가 타입, 파일 첨부 지원
- 출퇴근 기록: check-in/out 기록과 타입·시간 저장
- 공지 관리: 공지 작성 및 조회
- 권한 분리: 관리자/직원별 접근 제어
---

## 구현 흐름 및 통신 구조
```
[WPF Client]
   │  JSON/TCP
   ▼
[C++ TCP Server]  ──(TCP/JSON)──▶  [Python Scheduler]
   │                                   │
   └─────────────── SQL ───────────────┘
                    [MariaDB]
```
-C++ TCP Server: 클라이언트 요청 수신 → 데이터 검증 → DB 처리 → 필요 시 Python Scheduler 호출 → 결과 응답
-Python Scheduler: 규칙 기반 근무표 생성 → DB 저장
-MariaDB: 무결성·참조 제약 설계, 운영 데이터 저장

---
## 프로토콜 구조
### 핵심 프로토콜 예시  

>근무표 생성 (gen_timeTable)  
```
{
  "protocol": "gen_timeTable",
  "data": {
    "admin_uid": 1,
    "req_year": "2025",
    "req_month": "08",
    "team_uid": 1
  }
}
```
응답: { "protocol": "gen_timeTable", "resp": "success", "data": { "inserted": 310 } }
  
>근무표 수정 (mdf_scd)
```
{
  "protocol": "mdf_scd",
  "data": {
    "mdf_infos": [
      { "date": "2025-08-12", "staff_id": 3, "shift": "D" }
    ]
  }
}
```
응답: { "protocol": "mdf_scd", "resp": "success", "message": "1 row updated" }

>근무표 존재 여부 확인 (chk_timeTable)
```
{
  "protocol": "chk_timeTable",
  "data": { "team_uid": 1, "req_period": "2025-08" }
}
```
응답: { "protocol": "chk_timeTable", "resp": "success", "message": "exists" }

---
## DB ERD
 - team: 팀 정보
 - staff: 직원 정보(직급, 월 근무시간 등)
 - shift_code: 팀별 교대 코드/근무시간
 - schedule: 월간 근무표(직원+날짜 유니크)
 - duty_request: 근무 변경 요청(승인/반려/보류, 삭제 플래그)
 - handover_note: 인수인계(타입, 제목, 내용, 첨부)
 - check_in: 출퇴근 기록
 - notice: 공지사항


---
## 모델설명
 - Schedule Model: 팀/직원/날짜별 근무코드 저장, 유니크 키로 중복 배정 방지
 - DutyRequest Model: 변경 요청 내역과 상태 관리
 - HandoverNote Model: 인수인계 기록, 첨부파일 경로/이름 저장
 - CheckIn Model: 출퇴근 기록과 타입, 타임스탬프 관리
 - Notice Model: 공지사항 등록/조회

---
## 프로젝트 메인 디렉토리 구조
```
shifter/
├── Server_dev/                   # C++ TCP 서버 개발
│   ├── main.cpp # TCP서버 실행부, 프로토콜 분기
│   ├── TcpServer.cpp / TcpServer.h
│   ├── DBManager.cpp / DBManager.h
│   ├── ProtocolHandler.cpp / ProtocolHandler.h
│   └── struct.h  #공용 데이터 구조체
│
├── Admin_dev/                    # 관리자용 WPF 클라이언트
│    |── Models/ # 데이터 구조 정의
│    |── ViewModels # 화면별 ViewModel
│    |── Views    # UI 화면 (XAML)
│    ├── Enums    # 열거형(Enums)
│    ├── Helpers  # 값 변환기(Converter) 및 유틸리티
│    ├── Helpers  # 값 변환기(Converter) 및 유틸리티
│    |── Messages # MVVM 메시징 구조체
│    |── Resources/Services # MVVM 메시징 구조체
│    └──  Structs    # 전송용/공유용 구조체 정의

│
├── User_dev/                     # 직원용 WPF 클라이언트
│    ├── Views      # UI 화면 (XAML)
├    |── ViewModels # 화면별 ViewModel
├    |── Model      # 데이터 구조 정의
├    |── Services   # 서버 통신, 데이터 관리 로직
├    |── Helpers    # 값 변환기(Converter) 및 유틸리티
├    |── Messages   # MVVM 메시징 구조체
├    |── Enums      # 열거형(Enums)
└    └── Resources  # 이미지 및 리소스  
│
├── Python_tcp/                   # Python 스케줄러 & TCP 연동
│   ├── scheduler_app.py
│   └── requirements.txt
│
├── docs/                         # 개발 문서
│   ├── DemoScreenshot/
│   ├── DemoVideo/
│   ├── Database Schema Definition.pdf
│   ├── Development Schedule.pdf
│   ├── ERD.png
│   ├── Protocol Specification.pdf
│   └── System Architecture Diagram.png
│
├── README.md                     # 프로젝트 개요
└── LICENSE
```

