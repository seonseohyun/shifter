using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ShifterUser.Models
{
    public class DayDetailModel
    {
        public ConfirmedWorkScheModel? Schedule { get; set; }
        public AttendanceModel? Attendance { get; set; }
        public bool IsRequested { get; set; }
        public string? RequestReason { get; set; }
    }
}
