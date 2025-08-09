using ShifterUser.Enums;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ShifterUser.Helpers
{
    public interface IUserScheduleProvider
    {
        // 오늘/임의 날짜의 근무 타입을 얻는다.
        bool TryGetShiftType(DateTime date, out ShiftType shiftType);
    }
}