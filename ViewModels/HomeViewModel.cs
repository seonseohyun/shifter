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

            //AttendanceStatus = AttendanceStatus.출근완료;
        }

        // 바인딩 속성
        [ObservableProperty] private bool hasAlert = true;
        [ObservableProperty] private string todayDate;
        [ObservableProperty] private string teamName;
        [ObservableProperty] private string approvedText;
        [ObservableProperty] private string pendingText;
        [ObservableProperty] private string rejectedText;

        // enum 기반 출근 상태
        [ObservableProperty] private AttendanceStatus attendanceStatus;

        // 색상 바인딩용
        [ObservableProperty] private Brush attendanceColor = Brushes.Transparent;

        // 상태 변경 시 색상 자동 변경
        partial void OnAttendanceStatusChanged(AttendanceStatus value)
        {
            AttendanceColor = value switch
            {
                AttendanceStatus.출근완료 => Brushes.Green,
                AttendanceStatus.퇴근완료 => Brushes.Blue,
                _ => Brushes.Transparent
            };
        }

        // 텍스트 출력용
        public string AttendanceText => AttendanceStatus switch
        {
            AttendanceStatus.출근완료 => "출근 완료",
            AttendanceStatus.퇴근완료 => "퇴근 완료",
            _ => string.Empty
        };

        // 페이지 이동 커맨드
        [RelayCommand]
        private void OpenAlert() => MessageBox.Show("알림 페이지로 이동합니다.");

        [RelayCommand]
        private void GoToQrCheck()
            => WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.QR));

        [RelayCommand]
        private void GoToGroupActivity()
            => MessageBox.Show("그룹 활동 페이지로 이동합니다.");

        [RelayCommand]
        private void GoToNotice()
            => MessageBox.Show("공지사항 페이지로 이동합니다.");

        [RelayCommand]
        private void GoToHandover()
            => MessageBox.Show("인수인계 페이지로 이동합니다.");

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
