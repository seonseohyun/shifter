// Models/HandoverDetailModel.cs
using CommunityToolkit.Mvvm.ComponentModel;
using ShifterUser.Enums;
using System.Collections.ObjectModel;

namespace ShifterUser.Models
{
    public partial class HandoverDetailModel : ObservableObject
    {
        [ObservableProperty] private int handoverUid;
        [ObservableProperty] private string handoverTime = "";
        [ObservableProperty] private string author = "";
        [ObservableProperty] private ShiftType shiftType;
        [ObservableProperty] private HandoverType noteType;
        [ObservableProperty] private string title = "";
        [ObservableProperty] private string text = "";
        [ObservableProperty] private string textParticular = "";
        [ObservableProperty] private string additionalInfo = "";
        [ObservableProperty] private int isAttached;
        [ObservableProperty] private string fileName = "";

        // ★ 첨부 목록 (XAML ItemsControl 바인딩)
        public ObservableCollection<AttachmentModel> Attachments { get; } = new();
    }
}
