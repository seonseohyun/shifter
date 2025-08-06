using System;
using System.Globalization;
using System.Windows;
using System.Windows.Data;
using ShifterUser.Enums;

namespace ShifterUser.Converters
{
    public class ApprovedOrRejectedVisibilityConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is WorkRequestStatus status)
            {
                return (status == WorkRequestStatus.Approved || status == WorkRequestStatus.Rejected)
                    ? Visibility.Visible
                    : Visibility.Collapsed;
            }
            return Visibility.Collapsed;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}
