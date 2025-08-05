using System;
using System.Globalization;
using System.Windows.Data;
using System.Windows.Media.Imaging;
using ShifterUser.Enums;

namespace ShifterUser.Converters
{
    public class StatusToIconConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            string imagePath = value switch
            {
                WorkRequestStatus.Approved => "Resources/images/check_green.png",
                WorkRequestStatus.Rejected => "Resources/images/cancle_red.png",
                WorkRequestStatus.Pending => "Resources/images/pending.png",
                _ => "Resources/unknown.png"
            };

            return new BitmapImage(new Uri($"pack://application:,,,/{imagePath}"));
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => throw new NotImplementedException();
    }
}
