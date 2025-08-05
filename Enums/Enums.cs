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
        Goback
    }

    public enum ShiftType { Off, Day, Evening, Night }

    public enum WorkRequestStatus
    {
        Pending,  // 대기
        Approved, // 승인
        Rejected  // 반려
    }
}

