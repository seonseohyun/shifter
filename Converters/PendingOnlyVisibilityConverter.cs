using System;
using System.Globalization;
using System.Windows;
using System.Windows.Data;
using ShifterUser.Enums;

namespace ShifterUser.Converters
{
    public class PendingOnlyVisibilityConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is WorkRequestStatus status && status == WorkRequestStatus.Pending)
                return Visibility.Visible;
            return Visibility.Collapsed;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => throw new NotImplementedException();
    }
}
