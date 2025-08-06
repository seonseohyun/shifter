using ShifterUser.Enums;

public class WorkRequestModel
{
    public int Uid { get; set; }
    public DateTime RequestDate { get; set; }
    public ShiftType ShiftType { get; set; }
    public WorkRequestStatus Status { get; set; }
    public string Reason { get; set; }
    public string? RejectionReason { get; set; }

    public string StatusText => Status switch
    {
        WorkRequestStatus.Approved => "승인",
        WorkRequestStatus.Rejected => "반려",
        WorkRequestStatus.Pending => "대기",
        _ => "알수없음"
    };
}
