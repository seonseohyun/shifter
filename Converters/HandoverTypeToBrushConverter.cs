using ShifterUser.Enums;
using System;
using System.Globalization;
using System.Net.WebSockets;
using System.Windows.Data;
using System.Windows.Media;

namespace ShifterUser.Converters
{
    public class HandoverTypeToColorConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is HandoverType type)
            {
                return type switch
                {
                    HandoverType.교대 => new SolidColorBrush(Color.FromRgb(255, 143, 0)),     // 주황
                    HandoverType.출장 => new SolidColorBrush(Color.FromRgb(0, 122, 255)),     // 파랑
                    HandoverType.휴가및부재 => new SolidColorBrush(Color.FromRgb(76, 217, 100)), // 초록
                    HandoverType.퇴사 => new SolidColorBrush(Color.FromRgb(255, 59, 48)),     // 빨강
                    HandoverType.장비및물품 => new SolidColorBrush(Color.FromRgb(88, 86, 214)),  // 보라
                    HandoverType.기타 => new SolidColorBrush(Color.FromRgb(142, 142, 147)),   // 회색
                    _ => Brushes.Gray
                };
            }
            return Brushes.Gray;
        }
        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => throw new NotImplementedException();
    }
}
