using CommunityToolkit.Mvvm.ComponentModel;
using System;

namespace ShifterUser.Models
{
    public partial class AttendanceModel : ObservableObject
    {
        [ObservableProperty] private DateTime? clockInTime;
        [ObservableProperty] private string? clockInStatus;
        [ObservableProperty] private DateTime? clockOutTime;
        [ObservableProperty] private string? clockOutStatus;
    }
}
