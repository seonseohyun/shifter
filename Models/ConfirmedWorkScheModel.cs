using CommunityToolkit.Mvvm.ComponentModel;
using System;
using ShifterUser.Enums;


namespace ShifterUser.Models
{
    public partial class ConfirmedWorkScheModel : ObservableObject
    {
        [ObservableProperty] private ShiftType shiftType;
        [ObservableProperty] private TimeSpan startTime;
        [ObservableProperty] private TimeSpan endTime;
        [ObservableProperty] private string? groupName;

        // 근무 시간 Hours 자체로 바인딩
        [ObservableProperty] private double hours;



    }
}
