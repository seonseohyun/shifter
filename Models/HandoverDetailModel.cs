using CommunityToolkit.Mvvm.ComponentModel;
using ShifterUser.Enums;

namespace ShifterUser.Models
{
    public partial class HandoverDetailModel : ObservableObject
    {
        [ObservableProperty] private int handoverUid;
        [ObservableProperty] private string handoverTime = "";   // "2025-08-07 
        [ObservableProperty] private ShiftType shiftType;        // day/evening/night/off
        [ObservableProperty] private HandoverType noteType;      // 교대/출장/휴가
        [ObservableProperty] private string title = "";
        [ObservableProperty] private string text = "";
        [ObservableProperty] private string textParticular = "";
        [ObservableProperty] private string additionalInfo = "";
        [ObservableProperty] private int isAttached;             // 0/1 
        [ObservableProperty] private string fileName = "";
    }
}
