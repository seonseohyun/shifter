using ShifterUser.Enums;
using System;
using System.Globalization;
using System.Windows.Data;

namespace ShifterUser.Converters
{
    public class StatusToIconConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is WorkRequestStatus status)
            {
                return status switch
                {
                    WorkRequestStatus.Approved => "✔", // 또는 "\u2714"
                    WorkRequestStatus.Pending => "🕒", // 또는 "\u23F3"
                    WorkRequestStatus.Rejected => "✖", // 또는 "\u2716"
                    _ => ""
                };
            }
            return "";
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) => throw new NotImplementedException();
    }
}
