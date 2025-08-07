using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using ShifterUser.Models;
using System;
using System.Windows;
using System.Windows.Media;

namespace ShifterUser.ViewModels
{
    public partial class HomeViewModel : ObservableObject
    {
        private readonly UserSession _session;

        public HomeViewModel(UserSession session)
        {
            _session = session;

            // 초기화
            TeamName = _session.GetTeamName();
            TodayDate = _session.GetDate();

            var (approved, pending, rejected) = _session.GetRequestStatus();
            ApprovedText = $" 승인 {approved}건";
            PendingText = $" 대기 {pending}건";
            RejectedText = $" 반려 {rejected}건";

            var att = _session.GetAttendance();
            if (att != null)
            {
                if (att.ClockOutTime != null)
                    AttendanceStatus = AttendanceStatus.퇴근완료;
                else if (att.ClockInTime != null)
                    AttendanceStatus = AttendanceStatus.출근완료;
                else
                    AttendanceStatus = AttendanceStatus.출근전;
            }

        }

        // 바인딩 속성
        [ObservableProperty] private bool hasAlert = true;
        [ObservableProperty] private string todayDate;
        [ObservableProperty] private string teamName;
        [ObservableProperty] private string approvedText;
        [ObservableProperty] private string pendingText;
        [ObservableProperty] private string rejectedText;
        [ObservableProperty] private AttendanceStatus attendanceStatus = AttendanceStatus.출근전;

        [ObservableProperty]
        private Brush attendanceColor = Brushes.Gray;

        partial void OnAttendanceStatusChanged(AttendanceStatus value)
        {
            AttendanceColor = value switch
            {
                AttendanceStatus.출근완료 => Brushes.Green,
                AttendanceStatus.퇴근완료 => Brushes.Blue,
                AttendanceStatus.출근전 => Brushes.Gray,
                _ => Brushes.Transparent
            };
        }

        public string AttendanceText => AttendanceStatus switch
        {
            AttendanceStatus.출근완료 => "출근 완료",
            AttendanceStatus.퇴근완료 => "퇴근 완료",
            AttendanceStatus.출근전 => "출근 전입니다",
            _ => string.Empty
        };

        public void UpdateAttendanceStatusFromMessage(string message)
        {
            AttendanceStatus = message switch
            {
                        "출근 완료" => AttendanceStatus.출근완료,
                        "퇴근 완료" => AttendanceStatus.퇴근완료,
                        _ => AttendanceStatus.출근전
            };
        }

        // 페이지 이동 커맨드
        [RelayCommand]
        private void OpenAlert() => MessageBox.Show("알림 페이지로 이동합니다.");

        [RelayCommand]
        private void GoToQrCheck()
            => WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.QR));

        [RelayCommand]
        private void GoToGroupActivity()
        {
            Console.WriteLine("그룹 페이지로 이동합니다.");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.GroupDashboard));
        }

        [RelayCommand]
        private void GoToNotice()
        {
            Console.WriteLine("공지사항 페이지로 이동합니다.");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.GroupNotice));
        }

        [RelayCommand]
        private void GoToHandover()
        {
            Console.WriteLine("인수인계 페이지로 이동합니다.");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.GroupHandover));
        }

        [RelayCommand]
        private void GoToSchedule()
        {
            Console.WriteLine("스케줄 페이지로 이동합니다.");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.MySche));
        }

        [RelayCommand]
        private void GoToRequestStatus()
        {
            Console.WriteLine("근무 요청 페이지로 이동합니다.");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.ReqStatus));
        }
    }
}
