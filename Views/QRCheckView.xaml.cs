using OpenCvSharp;
using OpenCvSharp.Extensions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;
using ShifterUser.Converters;

namespace ShifterUser.Views
{
    public partial class QRCheckView : Page
    {
        private VideoCapture? _capture;
        private Mat _frame = new();
        private DispatcherTimer? _timer;

        public QRCheckView()
        {
            InitializeComponent();
            StartCamera();
            this.Unloaded += (s, e) => StopCamera();
        }

        private void StartCamera()
        {
            _capture = new VideoCapture(0);
            if (!_capture.IsOpened())
            {
                MessageBox.Show("카메라를 열 수 없습니다.");
                return;
            }

            _timer = new DispatcherTimer
            {
                Interval = TimeSpan.FromMilliseconds(33)
            };
            _timer.Tick += (s, e) =>
            {
                _capture.Read(_frame);
                if (!_frame.Empty())
                {
                    CameraPreview.Source = BitmapSourceConverter.ToBitmapSource(_frame);
                }
            };
            _timer.Start();
        }

        private void StopCamera()
        {
            _timer?.Stop();
            _capture?.Release();
            _frame?.Dispose();
        }
    }
}