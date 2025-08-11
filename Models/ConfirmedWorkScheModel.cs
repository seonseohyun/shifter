// ShifterUser.Models
using ShifterUser.Enums;
using System;

public partial class ConfirmedWorkScheModel
{
    public ShiftType ShiftType { get; set; }
    public string GroupName { get; set; } = "";

    public TimeSpan? StartTime { get; set; }
    public TimeSpan? EndTime { get; set; }

    // 총 근무시간 계산(자정 넘김 처리)
    public TimeSpan? Duration =>
        (StartTime.HasValue && EndTime.HasValue)
            ? (EndTime.Value >= StartTime.Value
                ? EndTime.Value - StartTime.Value
                : EndTime.Value.Add(TimeSpan.FromDays(1)) - StartTime.Value)
            : (TimeSpan?)null;

    // 시간대 + 총 근무시간
    public string HoursDetailDisplay
    {
        get
        {
            if (ShiftType == ShiftType.Off) return "-";
            if (!(StartTime.HasValue && EndTime.HasValue)) return "-";
            var dur = Duration ?? TimeSpan.Zero;
            if (dur.TotalMinutes <= 0) return "-";
            return $"{StartTime:hh\\:mm} - {EndTime:hh\\:mm} · {dur.TotalHours:0.#}시간";
        }
    }
}
