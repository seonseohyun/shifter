using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ShifterUser.Enums;
using CommunityToolkit.Mvvm.ComponentModel;

namespace ShifterUser.Models
{
    public partial class NoticeModel : ObservableObject
    {
        [ObservableProperty] private int noticeUid;
        [ObservableProperty] private string staffName = string.Empty;
        [ObservableProperty] private string noticeDate = string.Empty;
        [ObservableProperty] private string title = string.Empty;
    }
}


