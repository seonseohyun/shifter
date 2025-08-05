using ShifterUser.Enums;
using System;
using System.Globalization;
using System.Windows.Data;

namespace ShifterUser.Converters
{
    public class StatusToBoolConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is WorkRequestStatus status && parameter is string param)
            {
                return Enum.TryParse(typeof(WorkRequestStatus), param, out var result) && result?.Equals(status) == true;
            }
            return false;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) => throw new NotImplementedException();
    }
}
