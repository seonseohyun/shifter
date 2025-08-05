using ShifterUser.Enums;
using System;
using System.Globalization;
using System.Windows.Data;
using System.Windows.Media;

namespace ShifterUser.Converters
{
    public class StatusToColorConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is WorkRequestStatus status)
            {
                return status switch
                {
                    WorkRequestStatus.Approved => Brushes.Green,
                    WorkRequestStatus.Pending => Brushes.Gray,
                    WorkRequestStatus.Rejected => Brushes.Red,
                    _ => Brushes.Black,
                };
            }
            return Brushes.Black;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) => throw new NotImplementedException();
    }
}
