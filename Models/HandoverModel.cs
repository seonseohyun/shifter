using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ShifterUser.Enums;
using CommunityToolkit.Mvvm.ComponentModel;

namespace ShifterUser.Models
{
    public partial class HandoverModel : ObservableObject
    {
        [ObservableProperty] private int handoverUid;
        [ObservableProperty] private string name = "";
        [ObservableProperty] private string shiftDate = "";
        [ObservableProperty] private ShiftType shiftTime;
        [ObservableProperty] private HandoverType shiftTypeTag;
        [ObservableProperty] private string title = "";
    }
}



