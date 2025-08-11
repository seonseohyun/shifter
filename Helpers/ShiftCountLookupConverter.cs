using Shifter.Models;
using Shifter.ViewModels;
using System;
using System.Globalization;
using System.Linq;
using System.Windows.Data;

namespace Shifter.Helpers {
    public class ShiftCountLookupConverter : IMultiValueConverter {

        public object Convert(object[] values, Type targetType, object parameter, CultureInfo culture) {
            var daily = values[0] as DailyShiftStats;
            var code = values[1] as string;
            if (daily == null || string.IsNullOrEmpty(code)) return "";

            var returnvalue = daily.ShiftCounts.TryGetValue(code, out var cnt) ? cnt.ToString() : "";

            return returnvalue;

        }

        public object[] ConvertBack(object value, Type[] targetTypes, object parameter, CultureInfo culture)
            => throw new NotSupportedException();
    }

}
