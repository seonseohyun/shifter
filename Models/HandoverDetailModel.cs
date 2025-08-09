// Models/HandoverDetailModel.cs
using CommunityToolkit.Mvvm.ComponentModel;
using ShifterUser.Enums;
using System.Collections.ObjectModel;

namespace ShifterUser.Models
{
    public static class HandoverTypeMapper
    {
        public static string ToDisplay(HandoverType t) => t switch
        {
            HandoverType.교대 => "교대",
            HandoverType.출장 => "출장",
            HandoverType.휴가및부재 => "휴가/부재",
            HandoverType.퇴사 => "퇴사",
            HandoverType.장비및물품 => "장비/물품",
            _ => "기타"
        };
    }

    public partial class HandoverDetailModel : ObservableObject
    {
        [ObservableProperty] private int handoverUid;
        [ObservableProperty] private string handoverTime = "";
        [ObservableProperty] private string author = "";
        [ObservableProperty] private ShiftType shiftType;
        [ObservableProperty] private HandoverType noteType = HandoverType.기타;
        [ObservableProperty] private string title = "";
        [ObservableProperty] private string text = "";
        [ObservableProperty] private string textParticular = "";
        [ObservableProperty] private string additionalInfo = "";
        [ObservableProperty] private string? fileName;

        // 첨부 관련
        [ObservableProperty] private int isAttached; 
        public ObservableCollection<AttachmentModel> Attachments { get; } = new();
        // 서버로 보낼 표시용 문자
        public string NoteTypeDisplay => HandoverTypeMapper.ToDisplay(NoteType);
    }
}
