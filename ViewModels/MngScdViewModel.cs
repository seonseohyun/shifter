using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using Shifter.Enums;
using Shifter.Messages;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;

namespace Shifter.ViewModels {
    public partial class MngScdViewModel : ObservableObject {

        /** Constructor **/
        public MngScdViewModel(Session? session, ScdModel scdModel) {
            _session = session;
            _scdModel = scdModel;

            /* Temp Values */
            CompanyName  = "Company Name";
            TeamName     = "Team Name";
            AdminName    = "Admin Name";

            if( _session is not null ) {
                CompanyName = _session!.GetCurrentCompanyName();
                TeamName = _session!.GetCurrentTeamName();
                AdminName = _session!.GetCurrentAdminName();
            }

            /* Init Time */
            CurrentYear  = (int) DateTime.Now.Year;
            CurrentMonth = (int) DateTime.Now.Month;

            string? StrCurrentMonth = CurrentMonth < 10 ? "0" + CurrentMonth.ToString() : CurrentMonth.ToString();

            YearMonth = CurrentYear.ToString() + StrCurrentMonth;

            /* Get Admin Time Table */
            _ = LoadAsync(CurrentYear!.Value, CurrentMonth!.Value);
        }



        /** Member Variables **/
        /* Models DI */
        private readonly Session? _session;
        private readonly ScdModel _scdModel;

        int MonthChgCnt = 0;
        int YearChgCnt = 0;

        /* Title & Keywords */
        [ObservableProperty] private int? currentYear;
        [ObservableProperty] private int? currentMonth;
        [ObservableProperty] private string? yearMonth;
        [ObservableProperty] private string? companyName;
        [ObservableProperty] private string? teamName;
        [ObservableProperty] private string? adminName;

        /* Days for Creating ScheduleTable's Cells */
        public ObservableCollection<int> Days { get; } = new();

        /* Staff Schedules from Server */
        [ObservableProperty] private ObservableCollection<StaffSchedule> staffSchedules = new();

        /* ShiftCodes from Server */
        public static List<string> ShiftCodes { get; } = new();

        /* ShiftWorkingHoursMap from Server */
        public static Dictionary<string, int> ShiftWorkingHoursMap { get; } = new();

        /* ShiftHeaders from Server */
        public ObservableCollection<ShiftHeader> ShiftHeaders { get; } = new();

        /* Daily Statistics from Server */
        public ObservableCollection<DailyShiftStats> DailyStatistics { get; } = new();





        /** Member Methods **/


        /* Go to Check Changes Requirement */
        [RelayCommand] void GoToChkChgReq() {
            Console.WriteLine("[MngScdViewModel] Executed GoToChkChgReq()");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.ChkChgReq));
        }


        /* Go to Modify Schedule */
        [RelayCommand] void GoToMdfScd() {
            Console.WriteLine("[MngScdViewModel] Executed GoToMdfScd()");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.MdfScd));
        }


        /* Minus Month Commnad */
        [RelayCommand] void MinusMonth() {
            Console.WriteLine("[MngScdViewModel] Executed MinusMonth()");
            if (CurrentMonth > 1) {
                CurrentMonth--;
            } else {
                CurrentYear--;
                CurrentMonth = 12;
            }
            YearMonth = CurrentYear.ToString() + "년 " + CurrentMonth.ToString() + "월";
            _ = LoadAsync(CurrentYear!.Value, CurrentMonth!.Value);
        }


        /* Plus Month Command */
        [RelayCommand] void PlusMonth() {
            Console.WriteLine("[MngScdViewModel] Executed PlusMonth()");
            if (CurrentMonth < 12) {
                CurrentMonth++;
            } else {
                CurrentYear++;
                CurrentMonth = 1;
            }
            YearMonth = CurrentYear.ToString() + "년 " + CurrentMonth.ToString() + "월";
            _ = LoadAsync(CurrentYear!.Value, CurrentMonth!.Value);
        }


        /* Load Schedule Data from Server */
        private async Task LoadAsync(int year, int month) {
            Console.WriteLine($"[MngScdViewModel] Executed LoadAsync for {year}년 {month}월");
            // 1) 날짜 헤더는 UI 스레드에서
            await Application.Current.Dispatcher.InvokeAsync(() =>
            {
                Days.Clear();
                for (int d = 1; d <= DateTime.DaysInMonth(year, month); d++) Days.Add(d);
            });

            // 2) 서버에서 수신(백그라운드 OK)
            var list = await _scdModel.AskTimeTableAdminAsync(year, month);

            // 3) 이후의 모든 UI 바인딩 관련 갱신은 UI 스레드에서
            await Application.Current.Dispatcher.InvokeAsync(() =>
            {
                ShiftCodes.Clear();
                ShiftCodes.AddRange(_scdModel.LastShiftCodes);

                ShiftWorkingHoursMap.Clear();
                foreach (var kv in _scdModel.LastShiftHours)
                    ShiftWorkingHoursMap[kv.Key] = kv.Value;

                ShiftHeaders.Clear();
                foreach (var code in ShiftCodes) {
                    ShiftHeaders.Add(new ShiftHeader { ShiftCode = code, DisplayName = code });
                    Console.WriteLine($"[MngScd] items(days) = {Days.Count}");
                    Console.WriteLine($"[MngScd] server list count = {list?.Count}");
                    Console.WriteLine($"[MngScd] shift codes = {string.Join(",", _scdModel.LastShiftCodes ?? Array.Empty<string>())}");
                }

                OnPropertyChanged(nameof(ShiftHeaders));


                /* added */
                MdfScdViewModel.ShiftCodes.Clear();
                MdfScdViewModel.ShiftCodes.AddRange(ShiftCodes);

                MdfScdViewModel.ShiftWorkingHoursMap.Clear();
                foreach (var kv in ShiftWorkingHoursMap)
                    MdfScdViewModel.ShiftWorkingHoursMap[kv.Key] = kv.Value;


                StaffSchedules = new ObservableCollection<StaffSchedule>(list);

                InitializeStatistics();
                UpdateDailyStatistics();
            });
        }

        /* Initialize Daily Statitstics */
        private void InitializeStatistics() {
            Console.WriteLine("[MngScdViewModel] Executed InitializeStatistics");
            foreach (var staff in StaffSchedules) {
                if (staff.UpdateDailyStatsCallback == null)
                    staff.UpdateDailyStatsCallback = UpdateDailyStatistics;
                staff.ForceRecalc(); // TotalWorkingHours/TotalEmptyDays/ShiftCodeCounts 갱신
            }
            DailyStatistics.Clear();
            int dayCount = Days.Count;
            for (int day = 1; day <= dayCount; day++) {
                var stats = new DailyShiftStats { Day = day };
                foreach (var code in ShiftCodes) stats.ShiftCounts[code] = 0;
                foreach (var staff in StaffSchedules) {
                    var cell = staff.DailyShifts.FirstOrDefault(c => c.Day == day);
                    if (cell != null && !string.IsNullOrWhiteSpace(cell.ShiftCode)
                        && stats.ShiftCounts.ContainsKey(cell.ShiftCode))
                        stats.ShiftCounts[cell.ShiftCode]++;
                }
                DailyStatistics.Add(stats);
            }
            OnPropertyChanged(nameof(DailyStatistics));
        }

        private void UpdateDailyStatistics() => InitializeStatistics();


        // 월 바뀔 때 호출되도록 버튼 핸들러에서 LoadAsync 재호출
        /*
        partial void OnCurrentMonthChanged(int? value) {
            Console.WriteLine($"[MngScdViewModel] CurrentMonth changed: {value}");
            MonthChgCnt++;
            if( MonthChgCnt > 1 ) {
                if (CurrentYear is { } y && value is { } m) _ = LoadAsync(y, m);
            }
        }
        partial void OnCurrentYearChanged(int? value) {
            Console.WriteLine($"[MngScdViewModel] CurrentYear changed: {value}");
            if( YearChgCnt > 1 ) {
                if (value is { } y && CurrentMonth is { } m) _ = LoadAsync(y, m);
            }
        }
        */
    }
}
