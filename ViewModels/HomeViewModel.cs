using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using ShifterUser.Models;
using System;
using System.Windows;

namespace ShifterUser.ViewModels
{
    public partial class HomeViewModel : ObservableObject
    {
        private readonly UserSession _session;

        public HomeViewModel(UserSession session)
        {
            _session = session;

            // 세션에서 데이터 바인딩용 속성 초기화
            TeamName = _session.GetTeamName();

            var (approved, pending, rejected) = _session.GetRequestStatus();
            ApprovedText = $" 승인 {approved}건";
            PendingText = $" 대기 {pending}건";
            RejectedText = $" 반려 {rejected}건";
        }

        [ObservableProperty] private bool hasAlert = true;
        //  바인딩 속성 추가
        [ObservableProperty] private string teamName;
        [ObservableProperty] private string approvedText;
        [ObservableProperty] private string pendingText;
        [ObservableProperty] private string rejectedText;

        // 페이지 이동 
        [RelayCommand]
        private void OpenAlert()
        {
            MessageBox.Show("알림 페이지로 이동합니다.");
        }

        [RelayCommand]
        private void GoToQrCheck()
        {
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.QR));
        }

        [RelayCommand]
        private void GoToGroupActivity()
        {
            MessageBox.Show("그룹 활동 페이지로 이동합니다.");
        }

        [RelayCommand]
        private void GoToNotice()
        {
            MessageBox.Show("공지사항 페이지로 이동합니다.");
        }

        [RelayCommand]
        private void GoToHandover()
        {
            MessageBox.Show("인수인계 페이지로 이동합니다.");
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
