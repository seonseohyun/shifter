using ShifterUser.Enums;

public class WorkRequestModel
{
    public DateTime RequestDate { get; set; }
    public ShiftType ShiftType { get; set; }
    public WorkRequestStatus Status { get; set; }
    public string Reason { get; set; } // 작성 사유
    public string? RejectionReason { get; set; } // 반려일 경우만 존재
}
