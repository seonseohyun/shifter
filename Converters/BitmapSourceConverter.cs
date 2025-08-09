using OpenCvSharp;
using System.Drawing;
using System.Windows.Media.Imaging;
using System.IO;
using System.Windows;
using System.Windows.Interop;
using PixelFormat = System.Drawing.Imaging.PixelFormat;

namespace ShifterUser.Converters
{
    public static class BitmapSourceConverter
    {
        public static BitmapSource ToBitmapSource(this Mat mat)
        {
            using (var bitmap = OpenCvSharp.Extensions.BitmapConverter.ToBitmap(mat))
            {
                var hBitmap = bitmap.GetHbitmap();

                try
                {
                    return Imaging.CreateBitmapSourceFromHBitmap(
                        hBitmap,
                        IntPtr.Zero,
                        Int32Rect.Empty,
                        BitmapSizeOptions.FromEmptyOptions());
                }
                finally
                {
                    // 리소스 해제 (GDI 핸들 누수 방지)
                    NativeMethods.DeleteObject(hBitmap);
                }
            }
        }

        private static class NativeMethods
        {
            [System.Runtime.InteropServices.DllImport("gdi32.dll")]
            public static extern bool DeleteObject(IntPtr hObject);
        }
    }
}
