using ShifterUser.Enums;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ShifterUser.Helpers
{
    public static class ShiftTypeHelper
    {
        public static string ToKorean(this ShiftType type)
        {
            return type switch
            {
                ShiftType.Off => "휴무",
                ShiftType.Day => "주간",
                ShiftType.Evening => "저녁",
                ShiftType.Night => "야간",
                _ => "알 수 없음"
            };
        }
    }
}
