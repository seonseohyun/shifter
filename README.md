# 하루고리 이용자 프로그램 (ShifterUser)

하루고리(ShifterUser)는 근무자들이 **근무표 확인, 출퇴근 기록, 근무 변경 요청, 인수인계 작성/확인** 등의 업무를 간편하게 수행할 수 있도록 지원하는 WPF 기반 클라이언트 프로그램입니다.  
실시간 서버 통신을 통해 팀/그룹별 근무 일정과 요청 현황을 조회하고, 직관적인 UI로 업무 효율성을 높입니다.

## 주요 기능

### 1. 근무표 관리
- 주간/월간 근무표 조회: 서버에서 스케줄 데이터를 받아 달력 형태로 표시
- 근무 요약 팝업: 선택한 날짜의 근무 유형, 시간, 그룹, 출퇴근 기록 표시
- 근무 변경 요청: 변경 희망 날짜 및 유형을 서버에 요청

### 2. 출퇴근 관리
- 출근/퇴근 요청: `ask_check_in`, `ask_check_out` 프로토콜 기반 요청
- 출퇴근 현황 표시: 색상 점(Ellipse)과 상태 텍스트로 시각적 표시 (출근 전/출근 완료/퇴근 완료)
- 서버 상태 자동 반영: AttendanceChangedMessage 수신 시 ViewModel 갱신

### 3. 인수인계(Handover)
- 작성 기능: 교대 근무 시 업무 인수인계 작성
- 첨부파일 업로드: 사진, 문서 등 업무 참고자료 첨부
- AI 문장 정리 기능: 작성 내용을 AI로 가독성 있게 변환
- 상세보기: 이전 인수인계 내역 확인 및 파일 다운로드

### 4. 그룹/공지사항
- 그룹 활동 보기: 근무 그룹별 활동 현황 조회
- 공지사항 확인: 그룹 공지사항 목록 및 상세보기

### 5. 사용자 계정
- 로그인/로그아웃
- 내 정보 보기 / 수정
- 비밀번호 변경

## 기술 스택

| 영역        | 기술 |
|-------------|------|
| 프론트엔드(UI) | WPF (Windows Presentation Foundation) |
| 아키텍처     | MVVM (Model-View-ViewModel) |
| 언어         | C# (.NET) |
| 데이터 포맷  | JSON (Newtonsoft.Json) |
| 네트워크     | TCP 기반 Socket 통신 |
| 라이브러리   | CommunityToolkit.Mvvm, Newtonsoft.Json |

## 프로젝트 구조

ShifterUser/  
├── Views/             # UI 화면 (XAML)  
├── ViewModels/        # 화면별 ViewModel  
├── Models/            # 데이터 구조 정의  
├── Services/          # 서버 통신, 데이터 관리 로직  
├── Helpers/           # 값 변환기(Converter) 및 유틸리티  
├── Messages/          # MVVM 메시징 구조체  
├── Enums/             # 열거형(Enums)  
└── Resources/         # 이미지 및 리소스  

## 서버 통신 구조

- 프로토콜 기반 요청/응답  
  예) 근무표 요청
  ```json
  {
    "protocol": "ask_timetable_weekly",
    "data": {
      "date": "2025-08-11",
      "staff_uid": "1234"
    }
  }

 ## 실행 방법

1. 빌드 환경
   - .NET 6 이상
   - Visual Studio 2022

2. 빌드
   ```bash
   git clone [레포지토리 주소]
   cd ShifterUser
   dotnet build
