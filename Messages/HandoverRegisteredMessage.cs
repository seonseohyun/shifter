using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ShifterUser.Messages
{
    public sealed class HandoverRegisteredMessage
    {
        public int HandoverUid { get; }
        public HandoverRegisteredMessage(int handoverUid)
        {
            HandoverUid = handoverUid;
        }
    }

    // 팝업에서 "바로 보기" 눌렀을 때 상세로 이동하며 uid 넘기는 메시지
    public sealed class OpenHandoverDetailMessage
    {
        public int HandoverUid { get; }
        public OpenHandoverDetailMessage(int handoverUid)
        {
            HandoverUid = handoverUid;
        }
    }
}

