using ShifterUser.Enums;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ShifterUser.Models
{
    public class WorkScheReqModel
    {
    }

    public class CalendarDay
    {
        public DateTime Date { get; set; }
        public string DayText => Date.Day.ToString();
        public ShiftType Shift { get; set; }  // 여기에 근무 종류
        public bool IsWrited { get; set; }
    }
}
