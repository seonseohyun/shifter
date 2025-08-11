using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;

namespace Shifter.ViewModels {
    public partial class MdfScdViewModel : ObservableObject {

        /** Constructor **/
        public MdfScdViewModel(Session? session, ScdModel scdModel) {
            _session = session;
            _scdModel = scdModel;

            TeamName = _session?.GetCurrentTeamName();
            CompanyName = _session?.GetCurrentCompanyName();

            _ = LoadAsync(_session!.GetCurrentYear(), _session!.GetCurrentMonth()); 
        }



        /** Member Variables **/
        private readonly Session? _session;
        private readonly ScdModel _scdModel;

        [ObservableProperty] private string? teamName;
        [ObservableProperty] private string? companyName;
        [ObservableProperty] private string? yearMonth; // "2023-10" 형식
        [ObservableProperty] private string? adminName;
        public ObservableCollection<int> Days { get; set; } = new();
        [ObservableProperty] private ObservableCollection<StaffSchedule> staffSchedules = new();
        public static List<string> ShiftCodes { get; } = new();
        public static Dictionary<string, int> ShiftWorkingHoursMap { get; } = new();

        /* Header Shifts(Column Names) */
        public ObservableCollection<ShiftHeader> ShiftHeaders { get; set; } = new();
        public ObservableCollection<DailyShiftStats> DailyStatistics { get; set; } = new();



        /** Member Methods **/

        /* 클릭 시 Shift 변경 */
        [RelayCommand] public void ToggleShift(ScheduleCell cell) {
            Console.WriteLine("[MdfScdViewModel] Executed ToggleShift(ScheduleCell cell)");
            if (ShiftCodes.Count == 0) return;

            int currentIndex = ShiftCodes.IndexOf(cell.ShiftCode ?? "");
            int nextIndex = (currentIndex + 1) % ShiftCodes.Count;
            cell.ShiftCode = ShiftCodes[nextIndex];
            Console.WriteLine("[MdfScdViewModel] cell.ShiftCode:"+ cell.ShiftCode);
            UpdateDailyStatistics();
        }


        /* 스케줄 삭제 */
        [RelayCommand] public void DelScd() {
            Console.WriteLine("[MdfScdViewModel] Executed DelScd");
        }


        /* 스케줄 저장 */
        [RelayCommand] public void SaveScd() {
            Console.WriteLine("[MdfScdViewModel] Executed SaveScd()");
        }


        /* 스케줄 초기화 */
        public void UpdateDailyStatistics() {
            DailyStatistics.Clear();

            for (int day = 1; day <= 31; day++) {
                var stats = new DailyShiftStats { Day = day };

                // 모든 Shift에 대해 초기화
                foreach (var code in ShiftCodes)
                    stats.ShiftCounts[code] = 0;

                // 직원별로 해당 일자 셀을 찾아서 카운트
                foreach (var staff in StaffSchedules) {
                    var cell = staff.DailyShifts.FirstOrDefault(c => c.Day == day);
                    if (cell != null && ShiftCodes.Contains(cell.ShiftCode))
                        stats.ShiftCounts[cell.ShiftCode]++;
                }

                DailyStatistics.Add(stats);
            }

            OnPropertyChanged(nameof(DailyStatistics));
        }

        public async Task LoadAsync(int year, int month) {
            Console.WriteLine("[MdfScdViewModel] Executed LoadAsync(year: {0}, month: {1})", year, month);

            /* [1] 날짜 채우기 */
            Days.Clear();
            for (int i = 1; i <= (int) DateTime.DaysInMonth(year, month); i++)
                Days.Add(i);

            /* [2] Server, Py - Generate TimeTable 설정 */
            var list = await _scdModel.GenTimeTableAsync(year, month);

            await Application.Current.Dispatcher.InvokeAsync(() =>
            {
                /* [3] ShiftCodes, ShiftWorkingHoursMap 설정 */
                StaffSchedules = new ObservableCollection<StaffSchedule>(list);

                /* ShiftCodes, ShiftWorkingHoursMap 설정 */
                foreach (var schedule in StaffSchedules) {
                    schedule.UpdateDailyStatsCallback = UpdateDailyStatistics;
                    schedule.RebindAndRecalculate();   // ← 핵심
                }

                // 집계
                UpdateDailyStatistics();
            });
        }
    }
}
