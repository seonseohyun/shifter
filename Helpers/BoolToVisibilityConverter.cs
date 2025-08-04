using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Data;

namespace Shifter.Helpers {
    public class BoolToVisibilityConverter : IValueConverter {
        public bool Invert { get; set; } = false; // true면 반대로 동작

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture) {
            if (value is not bool boolValue)
                return DependencyProperty.UnsetValue;

            if (Invert)
                boolValue = !boolValue;

            return boolValue ? Visibility.Visible : Visibility.Collapsed;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) {
            if (value is not Visibility visibility)
                return DependencyProperty.UnsetValue;

            bool result = visibility == Visibility.Visible;
            return Invert ? !result : result;
        }
    }
}
