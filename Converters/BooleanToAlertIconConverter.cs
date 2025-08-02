using System;
using System.Globalization;
using System.Windows.Data;

namespace ShifterUser.Converters
{
    public class BooleanToAlertIconConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            bool hasAlert = value is bool b && b;
            return hasAlert ? "\uE7ED" : "\uE7ED"; // 알림 유무에 관계없이 같은 종. (모양 바꾸고 싶으면 수정)
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => throw new NotImplementedException();
    }
}
