using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using ShifterUser.Models;
using ShifterUser.Services;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls.Primitives;

namespace ShifterUser.ViewModels
{

    public partial class QRCheckViewModel : ObservableObject
    {
        private readonly AttendanceManager _manager;
        private readonly HomeViewModel _homeViewModel;

        public QRCheckViewModel(AttendanceManager Manager, HomeViewModel homeViewModel)
        {
            _manager = Manager;
            _homeViewModel = homeViewModel;
        }

        [RelayCommand]
        private static void GoBack()
        {
            WeakReferenceMessenger.Default.Send((new PageChangeMessage(PageType.Goback)));
        }

        [RelayCommand]
        private void CheckIn()
        {   
            // 출근 요청
            bool result = _manager.AskCheckIn(_homeViewModel);
            
            if (result)
            {
                MessageBox.Show($"출근 완료! {DateTime.Now:HH:mm}", "알림", MessageBoxButton.OK, MessageBoxImage.Information);
                WeakReferenceMessenger.Default.Send((new PageChangeMessage(PageType.Home)));
            }
            else
            {
                MessageBox.Show("출근 요청 실패했습니다.\n다시 시도해 주세요.", "오류", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        [RelayCommand]
        private void CheckOut()
        {
            // 퇴근 요청
            bool result = _manager.AskCheckOut(_homeViewModel); 

            if (result)
            {
                MessageBox.Show($"퇴근 완료! {DateTime.Now:HH:mm}", "알림", MessageBoxButton.OK, MessageBoxImage.Information);
                WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Home));
            }
            else
            {
                MessageBox.Show("퇴근 실패. 다시 시도해주세요.");
            }
        }

    }

}













