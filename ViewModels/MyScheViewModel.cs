using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using ShifterUser.Models;
using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace ShifterUser.ViewModels
{
    public partial class MyScheViewModel : ObservableObject
    {
        public MyScheViewModel(WorkScheReqModel scheModel, UserSession userSession)
        {
            Console.WriteLine("MyScheViewModel 생성됨");

            _scheModel = scheModel;
            _session = userSession;

            _currentDate = DateTime.Now;
            GenerateCalendar(_currentDate);
            UpdateSummary(); // 초기값 세팅
        }

        private WorkScheReqModel _scheModel;
        private UserSession _session;

        // 수정해야 됨
        [ObservableProperty]
        private int workDay = 10;

        [ObservableProperty]
        private int nightCnt = 8;

        [ObservableProperty]
        private int offCnt = 6;

        [ObservableProperty]
        private string scheduleSummaryText;

        // workDay가 바뀌면 호출됨
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

            // [1] Add Empty Cells
            for (int i = 0; i < skipDays; i++)
            {
                Days.Add(new DayModel { DayText = "" });
            }

            // [2] Add Actual Days
            for (int day = 1; day <= daysInMonth; day++)
            {
                var dayModel = new DayModel
                {
                    DayText = day.ToString(),
                    Date = new DateTime(targetDate.Year, targetDate.Month, day),
                   
                };

                Days.Add(dayModel);
            }
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
