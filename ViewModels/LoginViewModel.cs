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

namespace ShifterUser.ViewModels
{
    public partial class LoginViewModel : ObservableObject
    {
        public LoginViewModel(UserModel userModel)
        {
            _userModel = userModel;
        }
        
        UserModel _userModel;

        [ObservableProperty] private string? id;
        [ObservableProperty] private string? password;

        [RelayCommand]
        private void LogIn()
        {
            // 로그인 시 이메일과 비밀번호가 비어있는지 확인
            if (string.IsNullOrWhiteSpace(id) || string.IsNullOrWhiteSpace(Password))
            {
                MessageBox.Show("이메일과 비밀번호를 입력해주세요.", "입력 오류", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            // Model의 LogIn Method 사용
            bool LogInResult = _userModel.LogIn(id, Password);
            if (LogInResult is true)
            {
                MessageBox.Show($"로그인 성공! {id}님, 환영합니다.", "로그인 성공", MessageBoxButton.OK, MessageBoxImage.Information);
                GoToHome();
            }
        }

        [RelayCommand]
        private static void GoToInfo()
        {
            WeakReferenceMessenger.Default.Send((new PageChangeMessage(PageType.Info)));
        }

        private static void GoToHome()
        {
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Home));
        }
    }

}
