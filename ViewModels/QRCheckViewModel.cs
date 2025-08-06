using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using ShifterUser.Models;
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
        private readonly UserManager _userManager;
        public QRCheckViewModel(UserManager userManager )
        {
            _userManager = userManager;
        }

        [RelayCommand]
        private static void GoBack()
        {
            WeakReferenceMessenger.Default.Send((new PageChangeMessage(PageType.Goback)));
        }

        [RelayCommand]
        private void CheckIn()
        {
            bool result = _userManager.AskCheckIn(); // 서버 요청 전송
            if (result)
            {
                MessageBox.Show($"출근 완료! {DateTime.Now:HH:mm}", "알림", MessageBoxButton.OK, MessageBoxImage.Information);
                //Thread.Sleep(1000);
                WeakReferenceMessenger.Default.Send((new PageChangeMessage(PageType.Home)));
            }
            else
            {
                MessageBox.Show("출근 요청 실패했습니다.\n다시 시도해 주세요.", "오류", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

    }

}







