using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using ShifterUser.Models;
using ShifterUser.Services;
using System;
using System.Collections.ObjectModel;
using System.Net.Sockets;
using System.Threading.Tasks;
using ShifterUser.Helpers;

namespace ShifterUser.ViewModels
{
    public partial class MyScheViewModel : ObservableObject
    {
        public MyScheViewModel(WorkRequestManager scheModel, UserSession userSession, SocketManager socket)
        {
            Console.WriteLine("MyScheViewModel 생성됨");

            _socket = socket;
            _scheModel = scheModel;
            _session = userSession;

            _currentDate = DateTime.Now;
            GenerateCalendar(_currentDate);
            UpdateSummary();
        }

        private WorkRequestManager _scheModel;
        private UserSession _session;
        private SocketManager _socket;

        [ObservableProperty] private int workDay = 10;
        [ObservableProperty] private int nightCnt = 8;
        [ObservableProperty] private int offCnt = 6;
        [ObservableProperty] private string scheduleSummaryText;

        // 팝업 관련 프로퍼티 추가
        [ObservableProperty] private WorkRequestManager? selectedDayData;
        [ObservableProperty] private bool isDetailVisible;

        // 날짜 클릭 시 호출되는 커맨드
        /* 진또배기
        [RelayCommand]
        private async Task DayClick(DayModel day)
        {
            if (day.Date is null) return;

            Console.WriteLine($"[MyScheViewModel] {day.Date.Value:yyyy-MM-dd} 클릭됨");

            var newModel = new WorkRequestManager(_socket, _session);

            await newModel.LoadFromServerAsync(_session.GetUid(), day.Date.Value);

            SelectedDayData = newModel;
            IsDetailVisible = true;
        }
        */

        [RelayCommand]
        private async Task DayClick(DayModel day)
        {
            if (day.Date is null) return;

            Console.WriteLine($"[MyScheViewModel] {day.Date.Value:yyyy-MM-dd} 클릭됨");

            // 테스트 데이터 생성
            var testModel = new WorkRequestManager(_socket, _session)
            {
                Date = day.Date.Value,
                Schedule = new ConfirmedWorkScheModel
                {
                    ShiftType = ShiftType.Day,
                    StartTime = TimeSpan.Parse("09:00"),
                    EndTime = TimeSpan.Parse("18:00"),
                    GroupName = "테스트 근무조"
                },
                Attendance = new AttendanceModel
                {
                    ClockInTime = DateTime.Parse("2025-08-06 09:03"),
                    ClockOutTime = DateTime.Parse("2025-08-06 18:01")
                },
                IsRequested = true,
                RequestReason = "개인 사유"
            };

            SelectedDayData = testModel;
            IsDetailVisible = true;
        }

        partial void OnWorkDayChanged(int value) => UpdateSummary();
        partial void OnNightCntChanged(int value) => UpdateSummary();
        partial void OnOffCntChanged(int value) => UpdateSummary();

        private void UpdateSummary()
        {
            ScheduleSummaryText = $"     근무일 {WorkDay}일 / 야간 {NightCnt}일 / 휴무 {OffCnt}일";
        }

        public ObservableCollection<DayModel> Days { get; set; } = new ObservableCollection<DayModel>();

        private DateTime _currentDate;
        public string CurrentMonthText => $"{_currentDate:yyyy년 M월}";

        [RelayCommand]
        private void PreviousMonth()
        {
            _currentDate = _currentDate.AddMonths(-1);
            GenerateCalendar(_currentDate);
            OnPropertyChanged(nameof(CurrentMonthText));
        }

        [RelayCommand]
        private void NextMonth()
        {
            _currentDate = _currentDate.AddMonths(1);
            GenerateCalendar(_currentDate);
            OnPropertyChanged(nameof(CurrentMonthText));
        }

        private void GenerateCalendar(DateTime targetDate)
        {
            Days.Clear();

            DateTime firstDayOfMonth = new DateTime(targetDate.Year, targetDate.Month, 1);
            int daysInMonth = DateTime.DaysInMonth(targetDate.Year, targetDate.Month);
            int skipDays = (int)firstDayOfMonth.DayOfWeek;

            for (int i = 0; i < skipDays; i++)
                Days.Add(new DayModel { DayText = "" });

            for (int day = 1; day <= daysInMonth; day++)
            {
                Days.Add(new DayModel
                {
                    DayText = day.ToString(),
                    Date = new DateTime(targetDate.Year, targetDate.Month, day),
                });
            }
        }

        [RelayCommand]
        private void HideDetail()
        {
            IsDetailVisible = false;
        }

        [RelayCommand]
        private static void GoBack()
        {
            Console.WriteLine("[MyScheViewModel] GoBack command executed.");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Home));
        }
    }

    public partial class DayModel : ObservableObject
    {
        [ObservableProperty] private string? dayText;
        [ObservableProperty] private DateTime? date;
    }
}





