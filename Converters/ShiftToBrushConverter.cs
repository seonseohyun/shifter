using System;
using System.Globalization;
using System.Windows.Data;
using System.Windows.Media;

namespace ShifterUser.Converters
{
    public class ShiftToBrushConverter : IValueConverter
    {
        public Brush DayBrush { get; set; }
        public Brush EveBrush { get; set; }
        public Brush NightBrush { get; set; }
        public Brush OffBrush { get; set; }

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            var shift = value as string;
            if (string.IsNullOrWhiteSpace(shift)) return Brushes.Transparent;

            switch (shift.Trim().ToLower())
            {
                case "day":
                case "d": return DayBrush ?? Brushes.IndianRed;
                case "eve":
                case "evening":
                case "e": return EveBrush ?? Brushes.MediumSeaGreen;
                case "night":
                case "n": return NightBrush ?? Brushes.CornflowerBlue;
                case "off":
                case "o": return OffBrush ?? Brushes.Gray;
                default: return Brushes.Transparent;
            }
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => throw new NotSupportedException();
    }
}
