using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using ShifterUser.Models;
using ShifterUser.Services;
using ShifterUser.Helpers;
using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;

namespace ShifterUser.ViewModels
{
    public partial class MyScheViewModel : ObservableObject, IUserScheduleProvider
    {
        // ===== 주입 의존성 =====
        private readonly TimetableManager _tt;
        private readonly WorkRequestManager _scheModel; // (팝업 테스트용으로 유지)
        private readonly UserSession _session;
        private readonly SocketManager _socket;
        private readonly AttendanceManager _attendance;
        // ViewModels/MyScheViewModel.cs
        private readonly Dictionary<DateTime, ConfirmedWorkScheModel> _monthSchedule = new();


        // ===== 상태 =====
        private DateTime _currentDate = DateTime.Today;

        // 달력 셀
        public ObservableCollection<DayModel> Days { get; } = new();

        // 상단 요약 숫자
        [ObservableProperty] private int workDay;       // Day + Eve + Night
        [ObservableProperty] private int nightCnt;      // Night
        [ObservableProperty] private int offCnt;        // Off
        [ObservableProperty] private string scheduleSummaryText = ""; // "근무일 n일 · 야간 n일 · 휴무 n일"
        [ObservableProperty] private DayDetailModel? selectedDayData; 
        [ObservableProperty] private bool isDetailLoading;

        public IAsyncRelayCommand LoadOnAppearAsyncCommand { get; }

        [ObservableProperty] private bool isDetailVisible;

        // 상단 월 텍스트
        public string CurrentMonthText => $"{_currentDate:yyyy년 M월}";

        // ===== 생성자 =====
        public MyScheViewModel(TimetableManager tt, UserSession userSession, SocketManager socket, AttendanceManager attendance)
        {
            Console.WriteLine("MyScheViewModel 생성됨");

            _tt = tt;
            _session = userSession;
            _socket = socket;
            _attendance = attendance;

            _currentDate = DateTime.Today;

            GenerateCalendar(_currentDate);
            UpdateSummary();

            LoadOnAppearAsyncCommand = new AsyncRelayCommand(LoadOnAppearAsync);
        }

        // ===== 초기 로드 =====
        [RelayCommand]
        private async Task LoadOnAppearAsync()
        {
            await LoadTimeTableAsync(_currentDate);
        }

        // ===== 달력 생성 =====
        private void GenerateCalendar(DateTime targetDate)
        {
            Days.Clear();

            var firstDayOfMonth = new DateTime(targetDate.Year, targetDate.Month, 1);
            int daysInMonth = DateTime.DaysInMonth(targetDate.Year, targetDate.Month);
            int skipDays = (int)firstDayOfMonth.DayOfWeek; 

            // 앞 공백
            for (int i = 0; i < skipDays; i++)
                Days.Add(new DayModel { DayText = "" });

            // 실제 날짜
            for (int day = 1; day <= daysInMonth; day++)
            {
                Days.Add(new DayModel
                {
                    DayText = day.ToString(),
                    Date = new DateTime(targetDate.Year, targetDate.Month, day),
                    IsToday = DateTime.Today.Date == new DateTime(targetDate.Year, targetDate.Month, day)
                });
            }
        }

        // IUserScheduleProvider 구현
        public bool TryGetShiftType(DateTime date, out ShiftType shiftType)
        {
            // 월별 로드 이후 _monthSchedule에 캐시되어 있음
            if (_monthSchedule.TryGetValue(date.Date, out var sched))
            {
                shiftType = sched.ShiftType; // ConfirmedWorkScheModel.ShiftType (enum)
                return true;
            }

            // 캐시에 없을 경우 Days 컬렉션에서 보조 검색
            var hit = Days.FirstOrDefault(d => d.Date?.Date == date.Date);
            if (hit is not null && !string.IsNullOrWhiteSpace(hit.ShiftType))
            {
                shiftType = ParseShiftEnum(hit.ShiftType); // 이미 있는 유틸
                return true;
            }

            shiftType = ShiftType.Off;
            return false;
        }

        // ===== 서버에서 근무표 가져와서 Days에 매핑 =====
        private async Task LoadTimeTableAsync(DateTime month)
        {
            var list = await _tt.GetUserTimetableAsync(month.Year, month.Month);

            _monthSchedule.Clear();

            var map = list.ToDictionary(x => x.Date.Date, x => x);

            foreach (var cell in Days)
            {
                var key = cell.Date?.Date ?? default;
                if (key != default && map.TryGetValue(key, out var v))
                {
                    cell.ShiftType = v.Shift;        // "Day|Eve|Night|Off"
                    cell.Hours = v.Hours;
                    cell.ScheduleUid = v.ScheduleUid;
                    cell.HasShift = true;

                    //  월데이터엔 세부시간/그룹이 없으므로 기본값으로 캐시
                    _monthSchedule[key] = new ConfirmedWorkScheModel
                    {
                        ShiftType = ParseShiftEnum(v.Shift),
                        StartTime = TimeSpan.Zero,
                        EndTime = TimeSpan.Zero,
                        GroupName = null
                    };
                }
                else
                {
                    cell.ShiftType = null;
                    cell.Hours = 0;
                    cell.ScheduleUid = 0;
                    cell.HasShift = false;
                }
            }

            // shift 문자열을 모두 정규화해서 동일 기준으로 집계
            var normalized = list.Select(x => NormalizeShiftString(x.Shift)).ToList();

            WorkDay = normalized.Count(s => s is "Day" or "Eve" or "Night");
            NightCnt = normalized.Count(s => s == "Night");
            OffCnt = normalized.Count(s => s == "Off");

            UpdateSummary();

        }


        // ===== 날짜 클릭 → 팝업 =====
        [RelayCommand]
        private async Task DayClick(DayModel day)
        {
            if (day?.Date is null) return;
            var date = day.Date.Value;

            IsDetailVisible = true;
            IsDetailLoading = true;

            // 스케줄은 캐시에서
            _monthSchedule.TryGetValue(date.Date, out var schedule);

            // 출퇴근은 서버에서
            var attendance = await _attendance.GetByDateAsync(date);

            //  DayDetailModel로 바인딩
            SelectedDayData = new DayDetailModel
            {
                Schedule = schedule ?? new ConfirmedWorkScheModel(),
                Attendance = attendance ?? new AttendanceModel(),
                IsRequested = false,
                RequestReason = ""
            };

            IsDetailLoading = false;
        }


        [RelayCommand]
        private void HideDetail() => IsDetailVisible = false;

        // ===== 상단 요약 텍스트 =====
        partial void OnWorkDayChanged(int value) => UpdateSummary();
        partial void OnNightCntChanged(int value) => UpdateSummary();
        partial void OnOffCntChanged(int value) => UpdateSummary();

        private void UpdateSummary()
        {
            ScheduleSummaryText = $"     근무일 {WorkDay}일 / 야간 {NightCnt}일 / 휴무 {OffCnt}일";
        }

        // ===== 월 이동 =====
        [RelayCommand]
        private async Task PreviousMonth()
        {
            _currentDate = _currentDate.AddMonths(-1);
            GenerateCalendar(_currentDate);
            OnPropertyChanged(nameof(CurrentMonthText));
            await LoadTimeTableAsync(_currentDate);
        }

        [RelayCommand]
        private async Task NextMonth()
        {
            _currentDate = _currentDate.AddMonths(1);
            GenerateCalendar(_currentDate);
            OnPropertyChanged(nameof(CurrentMonthText));
            await LoadTimeTableAsync(_currentDate);
        }

        private static string NormalizeShiftString(string? s)
        {
            if (string.IsNullOrWhiteSpace(s)) return "";
            switch (s.Trim().ToUpperInvariant())
            {
                case "D":
                case "DAY": return "Day";
                case "E":
                case "EVE":
                case "EVENING": return "Eve";
                case "N":
                case "NIGHT": return "Night";
                case "O":
                case "OFF": return "Off";
                default: return s;
            }
        }

        private static ShiftType ParseShiftEnum(string? s)
        {
            var norm = NormalizeShiftString(s);
            return Enum.TryParse<ShiftType>(norm, true, out var r) ? r : ShiftType.Off;
        }

        // ===== 뒤로가기 =====
        [RelayCommand]
        private static void GoBack()
        {
            Console.WriteLine("[MyScheViewModel] GoBack command executed.");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Home));
        }


    }



    // ===== 달력 셀 모델 =====
    public partial class DayModel : ObservableObject
    {
        [ObservableProperty] private string? dayText;
        [ObservableProperty] private DateTime? date;

        // 칩(D/E/N/O) 바인딩
        [ObservableProperty] private string? shiftType;   // "Day|Eve|Night|Off"
        [ObservableProperty] private bool hasShift;
        [ObservableProperty] private int hours;
        [ObservableProperty] private int scheduleUid;

        [ObservableProperty] private bool isWrited = true;
        [ObservableProperty] private bool isToday;

    }
}
