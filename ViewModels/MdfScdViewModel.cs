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

namespace Shifter.ViewModels {
    public partial class MdfScdViewModel : ObservableObject {

        /** Constructor **/
        public MdfScdViewModel(Session? session) {
            _session = session;

            // [1] 날짜(1~31일) 채우기
            for (int i = 1; i <= 31; i++)
                Days.Add(i);

            // [2] 서버 또는 테스트용 Shift 정보 정의
            ShiftWorkingHoursMap.Clear();
            var testShiftInfos = new Dictionary<string, int>
                {
                    { "D", 8 },
                    { "E", 8 },
                    { "N", 8 },
                    { "O", 0 }
                };

            // [3] ShiftCode 리스트 및 ShiftHeader 초기화
            foreach (var kvp in testShiftInfos) {
                ShiftCodes.Add(kvp.Key);
                ShiftWorkingHoursMap[kvp.Key] = kvp.Value;

                // 동적 헤더용 (필요 시 사용)
                ShiftHeaders.Add(new ShiftHeader
                {
                    ShiftCode = kvp.Key,
                    DisplayName = $"{kvp.Key}"
                });
            }

            // [4] 테스트용 직원 스케줄 초기화
            for (int i = 1; i <= 24; i++) {
                var staff = new StaffSchedule { Name = $"staff{i}" };
                staff.UpdateDailyStatsCallback = UpdateDailyStatistics;

                for (int day = 1; day <= 31; day++) {
                    staff.DailyShifts.Add(new ScheduleCell { Day = day });
                }

                StaffSchedules.Add(staff);
            }

            UpdateDailyStatistics();
        }



        /** Member Variables **/
        private readonly Session? _session;
        public ObservableCollection<int> Days { get; set; } = new();
        [ObservableProperty] private ObservableCollection<StaffSchedule> staffSchedules = new();
        public static List<string> ShiftCodes { get; } = new();
        public static Dictionary<string, int> ShiftWorkingHoursMap { get; } = new();
        /* Header Shifts(Column Names) */
        public ObservableCollection<ShiftHeader> ShiftHeaders { get; set; } = new();
        public ObservableCollection<DailyShiftStats> DailyStatistics { get; set; } = new();



        /** Member Methods **/
        [RelayCommand] public void ToggleShift(ScheduleCell cell) {
            Console.WriteLine("[MdfScdViewModel] Executed ToggleShift(ScheduleCell cell)");
            if (ShiftCodes.Count == 0) return;

            int currentIndex = ShiftCodes.IndexOf(cell.ShiftCode ?? "");
            int nextIndex = (currentIndex + 1) % ShiftCodes.Count;
            cell.ShiftCode = ShiftCodes[nextIndex];
            Console.WriteLine("[MdfScdViewModel] cell.ShiftCode:"+ cell.ShiftCode);
            UpdateDailyStatistics();
        }

        [RelayCommand] public void DelScd() {
            Console.WriteLine("[MdfScdViewModel] Executed DelScd");
        }


        [RelayCommand] public void SaveScd() {
            Console.WriteLine("[MdfScdViewModel] Executed SaveScd()");
        }

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
    }



    /*** Class Schedule Cell ***/
    public partial class ScheduleCell : ObservableObject {
        
        /** Member Variables **/
        [ObservableProperty] private int day;
        private string shiftCode = "";
        public string ShiftCode {
            get => shiftCode;
            set {
                if (SetProperty(ref shiftCode, value)) {
                    ShiftCodeChanged?.Invoke(this, EventArgs.Empty);
                }
            }
        }
        public event EventHandler? ShiftCodeChanged;
    }




    /*** Class Staff Schedule ***/
    public partial class StaffSchedule : ObservableObject {
        
        /** Constructor **/
        public StaffSchedule() {
            DailyShifts.CollectionChanged += (s, e) => {
                if (e.NewItems != null)
                    foreach (ScheduleCell cell in e.NewItems)
                        cell.ShiftCodeChanged += OnCellShiftChanged;
                if (e.OldItems != null)
                    foreach (ScheduleCell cell in e.OldItems)
                        cell.ShiftCodeChanged -= OnCellShiftChanged;
            };
        }

        /* Member Variables */
        public string Name { get; set; } = string.Empty;
        public ObservableCollection<ScheduleCell> DailyShifts { get; set; } = new();
        // 동적 통계용 딕셔너리
        public ObservableCollection<KeyValuePair<string, int>> ShiftCodeCounts { get; set; } = new();
        public event EventHandler? ShiftChanged;
        public Action? UpdateDailyStatsCallback { get; set; }


        private void OnCellShiftChanged(object? sender, EventArgs e) {
            UpdateShiftCounts();
            OnPropertyChanged(nameof(TotalWorkingHours));
            OnPropertyChanged(nameof(TotalEmptyDays));
            UpdateDailyStatsCallback?.Invoke(); // ViewModel에 직접 요청
        }


        public void UpdateShiftCounts() {
            // 1. 임시 Dictionary로 그룹핑된 카운트 계산
            var tempDict = DailyShifts
                .GroupBy(c => c.ShiftCode)
                .Where(g => !string.IsNullOrWhiteSpace(g.Key))
                .ToDictionary(g => g.Key!, g => g.Count());

            // 2. 순서 맞춰 다시 채우기
            ShiftCodeCounts.Clear();

            foreach (var shift in MdfScdViewModel.ShiftCodes) {
                tempDict.TryGetValue(shift, out int count);
                ShiftCodeCounts.Add(new KeyValuePair<string, int>(shift, count));
            }

            OnPropertyChanged(nameof(ShiftCodeCounts));
        }

        public int TotalWorkingHours =>
            DailyShifts.Sum(c =>
                MdfScdViewModel.ShiftWorkingHoursMap.TryGetValue(c.ShiftCode ?? "", out int hours) ? hours : 0);

        public int TotalEmptyDays =>
            DailyShifts.Count(c => string.IsNullOrWhiteSpace(c.ShiftCode));
    }



    /*** Class ShiftHeader ***/
    public class ShiftHeader {
        public string DisplayName { get; set; } = "";   // 예: "Total D"
        public string ShiftCode { get; set; } = "";     // 예: "D"
    }


    /*** Class Daily Shift Status ***/
    public class DailyShiftStats : ObservableObject {
        public int Day { get; set; }

        // shift 코드 → 해당 일에 몇 명이 이 교대를 했는지
        public Dictionary<string, int> ShiftCounts { get; set; } = new();
    }

}
