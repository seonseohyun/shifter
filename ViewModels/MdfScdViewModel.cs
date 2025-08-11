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

            _ = LoadAsync(_session!.GetCurrentYear(), _session!.GetCurrentMonth());
            //// [1] 날짜(1~31일) 채우기
            //for (int i = 1; i <= 31; i++)
            //    Days.Add(i);

            //// [2] 서버 또는 테스트용 Shift 정보 정의
            //ShiftWorkingHoursMap.Clear();
            //var testShiftInfos = new Dictionary<string, int>
            //    {
            //        { "D", 8 },
            //        { "E", 8 },
            //        { "N", 8 },
            //        { "O", 0 }
            //    };

            //// [3] ShiftCode 리스트 및 ShiftHeader 초기화
            //foreach (var kvp in testShiftInfos) {
            //    ShiftCodes.Add(kvp.Key);
            //    ShiftWorkingHoursMap[kvp.Key] = kvp.Value;

            //    // 동적 헤더용 (필요 시 사용)
            //    ShiftHeaders.Add(new ShiftHeader
            //    {
            //        ShiftCode = kvp.Key,
            //        DisplayName = $"{kvp.Key}"
            //    });
            //}

            //// [4] 테스트용 직원 스케줄 초기화
            //for (int i = 1; i <= 24; i++) {
            //    var staff = new StaffSchedule { Name = $"staff{i}" };
            //    staff.UpdateDailyStatsCallback = UpdateDailyStatistics;

            //    for (int day = 1; day <= 31; day++) {
            //        staff.DailyShifts.Add(new ScheduleCell { Day = day });
            //    }

            //    StaffSchedules.Add(staff);
            //}

            //UpdateDailyStatistics();
        }



        /** Member Variables **/
        private readonly Session? _session;
        private readonly ScdModel _scdModel;
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
            var list = await _scdModel.GenTimeTableAsync(year, month);

            await Application.Current.Dispatcher.InvokeAsync(() =>
            {
                // 방법 A: 인스턴스 교체 (선택 유지가 필요 없다면 간단)
                StaffSchedules = new ObservableCollection<StaffSchedule>(list);

                // 각 항목에 콜백 연결
                foreach (var s in StaffSchedules)
                    s.UpdateDailyStatsCallback = UpdateDailyStatistics;

                // 집계
                UpdateDailyStatistics();
            });
        }
    }
}
