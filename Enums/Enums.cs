using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ShifterUser.Enums
{
    public enum PageType
    {
        Login,
        Home,
        Info,
        MySche,
        QR,
        ReqStatus,
        ReqSche,
        GroupDashboard,
        GroupHandover,
        Goback,
        GroupNotice,
        HandoverDetail
    }

    public enum ShiftType { Off, Day, Evening, Night }

    public enum WorkRequestStatus
    {
        Pending,  // 대기
        Approved, // 승인
        Rejected  // 반려
    }

    public enum AttendanceStatus
    {
        출근전,
        출근완료,
        퇴근완료
    }

    public enum HandoverType
    {
        교대,
        출장,
        휴가및부재,
        퇴사,
        장비및물품,
        기타
    }

}

