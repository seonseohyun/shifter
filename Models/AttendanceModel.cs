using CommunityToolkit.Mvvm.ComponentModel;
using ShifterUser.Enums;

namespace ShifterUser.Models
{

    public partial class AttendanceModel : ObservableObject
    {
        // ====== 서버 원본 값 ======
        [ObservableProperty]
        [NotifyPropertyChangedFor(nameof(IsClockInDone))]
        [NotifyPropertyChangedFor(nameof(ClockInTimeDisplay))]
        [NotifyPropertyChangedFor(nameof(ClockInStatusText))]
        [NotifyPropertyChangedFor(nameof(StatusDot))]
        private DateTime? clockInTime;

        [ObservableProperty]
        [NotifyPropertyChangedFor(nameof(IsClockInDone))]
        [NotifyPropertyChangedFor(nameof(ClockInStatusText))]
        [NotifyPropertyChangedFor(nameof(StatusDot))]
        private string? clockInStatus;

        [ObservableProperty]
        [NotifyPropertyChangedFor(nameof(IsClockOutDone))]
        [NotifyPropertyChangedFor(nameof(ClockOutTimeDisplay))]
        [NotifyPropertyChangedFor(nameof(ClockOutStatusText))]
        [NotifyPropertyChangedFor(nameof(StatusDot))]
        private DateTime? clockOutTime;

        [ObservableProperty]
        [NotifyPropertyChangedFor(nameof(IsClockOutDone))]
        [NotifyPropertyChangedFor(nameof(ClockOutStatusText))]
        [NotifyPropertyChangedFor(nameof(StatusDot))]
        private string? clockOutStatus;

        // ====== 계산 프로퍼티 ======
        public bool IsClockInDone =>
            !string.IsNullOrWhiteSpace(ClockInStatus)
                ? ClockInStatus.Equals("done", StringComparison.OrdinalIgnoreCase)
                : ClockInTime.HasValue;

        public bool IsClockOutDone =>
            !string.IsNullOrWhiteSpace(ClockOutStatus)
                ? ClockOutStatus.Equals("done", StringComparison.OrdinalIgnoreCase)
                : ClockOutTime.HasValue;

        public string ClockInTimeDisplay => ClockInTime?.ToString("HH:mm") ?? "--:--";
        public string ClockOutTimeDisplay => ClockOutTime?.ToString("HH:mm") ?? "--:--";

        public string ClockInStatusText => IsClockInDone ? "출근 완료" : "미출근";
        public string ClockOutStatusText => IsClockOutDone ? "퇴근 완료" : "미퇴근";

        // ★ 여기가 새로 추가되는 부분
        public AttendanceDot StatusDot =>
            IsClockOutDone ? AttendanceDot.Blue :
            IsClockInDone ? AttendanceDot.Green :
                             AttendanceDot.Gray;
    }
}
