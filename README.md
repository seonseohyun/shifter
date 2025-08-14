# shifter

Shifter(하루고리) – Admin
팀 근무표를 생성·조회·수정하는 WPF 기반 관리자 앱입니다.
 서버와 소켓(JSON 프로토콜)으로 통신해 스케줄을 받아오고, UI에서 변경한 셀만 묶어 저장합니다.

주요 기능
월별 근무표 조회(MngScdView)
셀은 텍스트로 표시(조회 전용)
좌측: 직원, 상단: 1~31일, 우측: 개인별 집계(근무시간/잔여/Shift별 합계)
하단: 일자별 집계(Shift별 인원 수)


근무표 수정(MdfScdView)
셀 클릭 시 ShiftCode 순환(D/E/N/O 등)
변경된 셀만 취합하여 mdf_scd 프로토콜로 저장
변경 하이라이트, 집계 자동 갱신


근무표 생성/요청
gen_timeTable: 서버에 월별 자동 배치 생성 요청
ask_timetable_admin: 기존 스케줄 조회 요청


월 이동/네비게이션
＜ / ＞ 로 월 변경
메시지버스(CommunityToolkit.Mvvm.Messaging)로 페이지 전환



기술 스택
.NET / WPF (권장: .NET 6+ / VS 2022)
MVVM (CommunityToolkit.Mvvm)
JSON 파싱 (Newtonsoft.Json)
소켓 통신 (커스텀 SocketManager, WorkItem)



화면 구성
MngScdView: 조회 전용 화면
날짜 헤더 / 본문(직원×일자) / 하단(일별 합계) 3행 Grid
스크롤뷰어는 본문(Row 1, *)이 공간을 차지하도록 구성




MdfScdView: 수정 화면
셀 클릭 → ShiftCode 순환 → 변경 사항 집계/저장


ChkChgReqView(예정/옵션): 변경 요청 검토



아키텍처 개요
scss
복사편집
Views (XAML)
  ├─ MngScdView (조회)
  └─ MdfScdView (수정)
ViewModels (MVVM Toolkit)
  ├─ MngScdViewModel
  └─ MdfScdViewModel
Models
  ├─ ScdModel         // 서버 통신, 파싱
  ├─ StaffSchedule    // 한 직원의 월간 스케줄 + 우측 집계
  ├─ ScheduleCell     // 일자별 셀(ShiftCode 등)
  ├─ ShiftHeader      // 우측/하단 헤더
  └─ DailyShiftStats  // 하단 일자별 집계
Infra
  ├─ SocketManager    // Send/Receive(WorkItem)
  └─ Session          // 현재 팀/회사/연월 등 컨텍스트


데이터 모델 (요약)
StaffSchedule
StaffId, Name
ObservableCollection<ScheduleCell> DailyShifts
우측 집계:
int TotalWorkingHours
int TotalEmptyDays(또는 RemainHours 도입 가능)
ObservableCollection<KeyValuePair<string,int>> ShiftCodeCounts
ForceRecalc()로 전체 재계산


ScheduleCell
int Day, string? ShiftCode
event ShiftCodeChanged (셀 값 변경 감지)
(선택) OriginalShiftCode, IsDirty로 변경 추적


DailyShiftStats
int Day, Dictionary<string,int> ShiftCounts


ShiftHeader
ShiftCode, DisplayName (예: Total\nShift1)



서버 통신 & 프로토콜
모든 요청/응답은 WorkItem으로 주고받으며, 본문은 JSON입니다.
공통 WorkItem 구조
json
복사편집
{
  "json": "{...}",  // 실제 프로토콜 JSON 문자열
  "payload": "..."  // (옵션) 바이너리
}

1) 근무표 생성 요청: gen_timeTable
요청
json
복사편집
{
  "protocol": "gen_timeTable",
  "data": {
    "admin_uid": 123,
    "team_uid":  1,
    "req_year":  "2025",
    "req_month": "08"
  }
}

성공 응답(예)
json
복사편집
{
  "protocol": "gen_timeTable",
  "resp": "success",
  "data": [
    {
      "date": "2025-08-01",
      "shift": "D",
      "hours": 8,
      "people": [
        {"staff_id": 3, "name": "박경태", "grade": 3},
        ...
      ]
    },
    ...
  ]
}

2) 근무표 조회 요청: ask_timetable_admin
요청
json
복사편집
{
  "protocol": "ask_timetable_admin",
  "data": {
    "req_year": "2025",
    "req_month": "08",
    "team_uid": 1
  }
}

성공 응답(예)
data 배열(또는 루트 배열)로 동일 구조의 항목이 내려옴


앱은 응답에서 Shift 목록/시간을 수집해 ShiftCodes, ShiftWorkingHoursMap을 채움


3) 변경 저장: mdf_scd
요청(변경분만)
json
복사편집
{
  "protocol": "mdf_scd",
  "data": {
    "mdf_infos": [
      { "date": "2025-08-03", "staff_id": 7, "shift": "E" },
      { "date": "2025-08-05", "staff_id": 2, "shift": "O" }
    ]
  }
}

성공 응답
json
복사편집
{ "protocol": "mdf_scd", "resp": "success", "message": "..." }

참고: 일부 서버 로그에서 루트가 배열이거나 꼬리 문자열이 붙을 수 있어 방어 파싱을 구현했습니다.

빌드 & 실행
요구 사항


Visual Studio 2022 이상


.NET SDK 6 이상


복제 후 빌드


VS로 솔루션 열기 → Release 또는 Debug 빌드


서버 연결 설정


SocketManager/Session의 엔드포인트, 인증(있다면)을 프로젝트 설정 또는 코드 상수로 지정


실행


F5 (디버그) 또는 빌드 산출물 실행



사용법 (핵심 흐름)
조회(MngScd)


상단 월 네비게이션으로 연/월 선택
자동으로 서버에 ask_timetable_admin 요청
수신 데이터 렌더링 + 우측/하단 집계 표시


수정(MdfScd)


Modify Schedule → MdfScd 화면 진입
셀 클릭으로 ShiftCode 순환
저장하기 → 변경분만 mdf_scd로 전송
성공 시 원본 상태 갱신



트러블슈팅
Send가 두 번 호출됨
월 변경 시 버튼에서 LoadAsync 호출 + OnCurrentMonth/YearChanged에서 다시 호출 → 한 곳으로 통합하세요(버튼만 or partial 메서드만).
동시 변경 방지용으로 ReloadAsync(re-entrancy guard) 추천.


집계(우측/하단)가 비어 있음
ShiftCodes/ShiftWorkingHoursMap이 비어있는 상태에서 집계 함수 호출됐을 가능성 → Shift 기준을 먼저 세팅한 뒤 InitializeStatistics()/UpdateDailyStatistics() 호출.


ShiftCodeCounts는 ObservableCollection<KeyValuePair<string,int>> 권장(딕셔너리 직접 바인딩 X).


스크롤뷰어 높이가 비정상(매우 얇음)
하단 합계의 큰 마진(Margin="0,240,0,0")을 Auto Row가 먹어버림 → 날짜/본문/합계를 3행 Grid로 분리, 본문은 * 높이.


레이아웃이 겹쳐 보임
내부 Schedule Grid에 RowDefinitions가 없거나 모든 자식이 같은 Grid.Row → 0/1/2로 분리.


UI 갱신 안 됨 / 무응답
바인딩된 컬렉션 업데이트는 Dispatcher(UI 스레드) 에서 실행.


서버 응답 파싱 오류
루트가 배열이거나 꼬리 문자열(TPTP 등)이 존재할 수 있음 → JToken.Parse 예외 시 마지막 }/]까지 잘라 재파싱.



개발 노트
집계 순서:
서버에서 스케줄 수신
Shift 기준(코드/시간) 세팅
StaffSchedules 바인딩
ForceRecalc()로 행 집계
UpdateDailyStatistics()로 일별 집계


UI 일관성:
날짜 셀(폭 26), 우측 헤더/값(근무/잔여 60, 각 Total 36) 폭 맞춤
헤더와 본문 폭이 다르면 정렬 틀어짐


확장 아이디어:
헤더/좌측 고정(Freeze), 주말/공휴일 색 구분
변경 내역 미리보기/되돌리기
CSV/Excel 내보내기
대용량 가상화(VirtualizingStackPanel)



폴더 구조(예시)
pgsql
복사편집
Shifter.Admin/
  Views/
    MngScdView.xaml
    MdfScdView.xaml
  ViewModels/
    MngScdViewModel.cs
    MdfScdViewModel.cs
  Models/
    ScdModel.cs
    StaffSchedule.cs
    ScheduleCell.cs
    ShiftHeader.cs
    DailyShiftStats.cs
  Infra/
    SocketManager.cs
    WorkItem.cs
    Session.cs
  Resources/
    Styles.xaml
    Icons/


라이선스
사내 프로젝트(또는 라이선스 넣기). 필요 시 LICENSE 파일 추가.

문의
버그/제안은 이슈에 남겨 주세요.
 UI/프로토콜/스케줄 로직 변경 시 README와 주석도 함께 업데이트 부탁드립니다. 🙌


