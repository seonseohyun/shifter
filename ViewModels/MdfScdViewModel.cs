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

            CompanyName = _session?.GetCurrentCompanyName();
            TeamName = _session?.GetCurrentTeamName();
            YearMonth = _session?.GetCurrentYear().ToString() + _session?.GetCurrentMonth().ToString();
            AdminName = _session?.GetCurrentAdminName();

            _ = LoadAsync(_session!.GetCurrentYear(), _session!.GetCurrentMonth()); 
        }



        /** Member Variables **/
        /* Model DI */
        private readonly Session? _session;
        private readonly ScdModel _scdModel;

        /* Title & Keywords */
        [ObservableProperty] private string? companyName;
        [ObservableProperty] private string? teamName;
        [ObservableProperty] private string? yearMonth; // "2023-10" 형식
        [ObservableProperty] private string? adminName;

        /* For ScheduleTable */
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


        /* LoadAsync - 서버로부터 날짜, 시간표 불러오기 */
        public async Task LoadAsync(int year, int month) {
            Console.WriteLine("[MdfScdViewModel] Executed LoadAsync(year: {0}, month: {1})", year, month);

            /* [1] 날짜 채우기 */
            Days.Clear();
            for (int i = 1; i <= (int) DateTime.DaysInMonth(year, month); i++)
                Days.Add(i);

            /* [2] Server, Py - Generate TimeTable 설정 */
            var list = await _scdModel.GenTimeTableAsync(year, month);

            // 2-1) ShiftCodes / Hours 주입
            ShiftCodes.Clear();
            foreach (var code in _scdModel.LastShiftCodes)
                ShiftCodes.Add(code);

            ShiftWorkingHoursMap.Clear();
            foreach (var kv in _scdModel.LastShiftHours)
                ShiftWorkingHoursMap[kv.Key] = kv.Value;

            // 2-2) 하단 표의 왼쪽 레이블(헤더) 구성
            ShiftHeaders.Clear();
            foreach (var code in ShiftCodes) {
                ShiftHeaders.Add(new ShiftHeader
                {
                    ShiftCode = code,
                    DisplayName = code   // 필요 시 "주간(D)" 등으로 표시명 매핑
                });
            }
            OnPropertyChanged(nameof(ShiftHeaders));

            // 2-3) 직원 스케줄 바인딩
            StaffSchedules = new ObservableCollection<StaffSchedule>(list);

            // 2-4) 행 강제 재계산 및 하단 집계
            InitializeStatistics();
            UpdateDailyStatistics();
        }


        /* Renew Cells */
        public void InitializeStatistics() {
            // 1) 각 행 강제 집계(총 근무시간/빈 칸/행별 코드 카운트)
            foreach (var staff in StaffSchedules) {
                // 콜백 연결(없으면 생략 가능)
                if (staff.UpdateDailyStatsCallback == null)
                    staff.UpdateDailyStatsCallback = UpdateDailyStatistics;

                // 행 상태 강제 갱신 (StaffSchedule 쪽에 메서드 하나 있어야 편함)
                staff.ForceRecalc();   // 아래 참고
            }

            // 2) 하단 일별 통계 갱신
            DailyStatistics.Clear();

            // 31 고정 대신 뷰에 있는 Days 사용 (없으면 DaysInMonth)
            int dayCount = Days?.Count > 0 ? Days.Count : 31;

            for (int day = 1; day <= dayCount; day++) {
                var stats = new DailyShiftStats { Day = day };

                // 모든 코드 0으로 초기화
                foreach (var code in ShiftCodes)
                    stats.ShiftCounts[code] = 0;

                // 직원별 셀 확인
                foreach (var staff in StaffSchedules) {
                    var cell = staff.DailyShifts.FirstOrDefault(c => c.Day == day);
                    if (cell != null && !string.IsNullOrWhiteSpace(cell.ShiftCode) && stats.ShiftCounts.ContainsKey(cell.ShiftCode))
                        stats.ShiftCounts[cell.ShiftCode]++;
                }

                DailyStatistics.Add(stats);
            }

            OnPropertyChanged(nameof(DailyStatistics));
        }
    }
}
