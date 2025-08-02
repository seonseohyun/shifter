using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using System.Windows;

namespace ShifterUser.ViewModels
{
    public partial class HomeViewModel : ObservableObject
    {
        [ObservableProperty]
        private bool hasAlert = true;

        [RelayCommand]
        private void OpenAlert()
        {
            MessageBox.Show("알림 페이지로 이동합니다.");
        }

        [RelayCommand]
        private void GoToQrCheck()
        {
            MessageBox.Show("QR 체크 페이지로 이동합니다.");
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
            MessageBox.Show("스케줄 페이지로 이동합니다.");
        }

        [RelayCommand]
        private void GoToRequestStatus()
        {
            MessageBox.Show("근무 요청 현황 페이지로 이동합니다.");
        }
    }
}
