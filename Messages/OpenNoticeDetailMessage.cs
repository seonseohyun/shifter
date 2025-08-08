using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.Messaging.Messages;

namespace ShifterUser.Messages
{

    public sealed class OpenNoticeDetailMessage : ValueChangedMessage<int>
    {
        public OpenNoticeDetailMessage(int noticeUid) : base(noticeUid) { }
    }
}
