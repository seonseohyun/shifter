using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Data;

namespace Shifter.Helpers {
    public class ShiftCountLookupConverter : IMultiValueConverter {
        public object Convert(object[] values, Type targetType, object parameter, CultureInfo culture) {
            if (values.Length < 2 || values[0] is not Dictionary<string, int> dict || values[1] is not string code) { 
                Console.WriteLine("[ShiftCountLookupConverter]");
                return "0";
            }

            return dict.TryGetValue(code, out int count) ? count.ToString() : "0";
        }

        public object[] ConvertBack(object value, Type[] targetTypes, object parameter, CultureInfo culture)
            => throw new NotImplementedException();
    }

}
