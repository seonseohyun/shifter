using System;
using System.Globalization;
using System.Text.RegularExpressions;
using System.Windows.Data;

namespace ShifterUser.Converters
{
    public class NewlineUnescapeConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            var s = value?.ToString() ?? string.Empty;

            // JSON에서 넘어올 때 실제 개행/CR 혼재 → 통일
            s = s.Replace("\r\n", "\n").Replace("\r", "\n").Replace("\n", Environment.NewLine);

            // 문자 그대로의 \r\n, \n, \t → 실제 제어문자로
            s = s.Replace("\\r\\n", Environment.NewLine)
                 .Replace("\\n", Environment.NewLine)
                 .Replace("\\t", "\t");

            return s;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => value; // 역변환 불필요
    }
}
