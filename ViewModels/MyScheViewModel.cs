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
        private readonly UserSession _session;
        private readonly SocketManager _socket;
        private readonly AttendanceManager _attendance;
        private readonly Dictionary<DateTime, ConfirmedWorkScheModel> _monthSchedule = new();


        // ===== 상태 =====
        private DateTime _currentDate = DateTime.Today;

        // 달력 셀
        public ObservableCollection<DayModel> Days { get; } = new();

        // 상단 요약 숫자
        [ObservableProperty] private int workDay;
        [ObservableProperty] private int nightCnt;      
        [ObservableProperty] private int offCnt;       
        [ObservableProperty] private string scheduleSummaryText = ""; 
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
            await _tt.EnsureShiftRulesAsync();
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
                shiftType = ParseShiftEnum(hit.ShiftType); 
                return true;
            }

            shiftType = ShiftType.Off;
            return false;
        }

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
                    cell.ShiftType = v.Shift;     
                    cell.Hours = v.Hours;
                    cell.ScheduleUid = v.ScheduleUid;
                    cell.HasShift = true;

                    var st = ParseShiftEnum(v.Shift);
                    var sched = new ConfirmedWorkScheModel
                    {
                        ShiftType = st,
                        GroupName = _session.GetTeamName()
                    };

                    var code = TimetableManager.ToCode(st);
                    if (_tt.TryGetShiftRule(code, out var rule))
                    {
                        sched.StartTime = rule.Start;
                        sched.EndTime = rule.End;
                    }

                    _monthSchedule[key] = sched;
                }
                else
                {
                    cell.ShiftType = null;
                    cell.Hours = 0;
                    cell.ScheduleUid = 0;
                    cell.HasShift = false;
                }
            }

            var normalized = list.Select(x => NormalizeShiftString(x.Shift)).ToList();
            WorkDay = normalized.Count(s => s is "Day" or "Eve" or "Night");
            NightCnt = normalized.Count(s => s == "Night");
            OffCnt = normalized.Count(s => s == "Off");
            UpdateSummary();
        }

        [RelayCommand]
        private async Task DayClick(DayModel day)
        {
            if (day?.Date is null) return;
            var date = day.Date.Value;

            IsDetailVisible = true;
            IsDetailLoading = true;

            _monthSchedule.TryGetValue(date.Date, out var schedule);

            // 혹시 캐시에 시간 미적용이면 여기서 한 번 더
            if (schedule is not null && schedule.StartTime is null)
            {
                var code = TimetableManager.ToCode(schedule.ShiftType);
                if (_tt.TryGetShiftRule(code, out var rule))
                {
                    schedule.StartTime = rule.Start;
                    schedule.EndTime = rule.End;
                }
            }

            var attendance = await _attendance.GetByDateAsync(date);

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

        private static ShiftType ParseShiftEnum(string? s) => (s ?? "").Trim().ToUpperInvariant() switch
        {
            "D" or "DAY" => ShiftType.Day,
            "E" or "EVENING" => ShiftType.Evening,
            "N" or "NIGHT" => ShiftType.Night,
            "O" or "OFF" or "-" or "" => ShiftType.Off,
            _ => ShiftType.Off
        };

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
