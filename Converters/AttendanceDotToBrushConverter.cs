using System;
using System.Globalization;
using System.Windows.Data;
using System.Windows.Media;
using ShifterUser.Enums;

namespace ShifterUser.Converters
{
    public class AttendanceDotToBrushConverter : IValueConverter
    {
        public Color GrayColor { get; set; } = (Color)ColorConverter.ConvertFromString("#BDBDBD");
        public Color GreenColor { get; set; } = (Color)ColorConverter.ConvertFromString("#00C853");
        public Color BlueColor { get; set; } = (Color)ColorConverter.ConvertFromString("#2979FF");

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            // 값형 enum은 'as' 대신 패턴 매칭 사용
            var dot = value is AttendanceDot d ? d : AttendanceDot.Gray;

            var color = dot switch
            {
                AttendanceDot.Blue => BlueColor,
                AttendanceDot.Green => GreenColor,
                _ => GrayColor
            };
            return new SolidColorBrush(color);
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => throw new NotSupportedException();
    }
}
