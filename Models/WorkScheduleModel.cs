using CommunityToolkit.Mvvm.ComponentModel;
using System;
using ShifterUser.Enums;


namespace ShifterUser.Models
{
    public partial class WorkScheduleModel : ObservableObject
    {
        [ObservableProperty] private ShiftType shiftType;
        [ObservableProperty] private TimeSpan startTime;
        [ObservableProperty] private TimeSpan endTime;
        [ObservableProperty] private string groupName;
    }
}
