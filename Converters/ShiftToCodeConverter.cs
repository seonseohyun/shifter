// Converters/ShiftToCodeConverter.cs
using System;
using System.Globalization;
using System.Windows.Data;

namespace ShifterUser.Converters
{
    public class ShiftToCodeConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            var s = value as string;
            if (string.IsNullOrWhiteSpace(s)) return "";
            switch (s.Trim().ToLower())
            {
                case "day":
                case "d": return "D";
                case "eve":
                case "evening":
                case "e": return "E";
                case "night":
                case "n": return "N";
                case "off":
                case "o": return "O";
                default: return "";
            }
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => throw new NotSupportedException();
    }
}
