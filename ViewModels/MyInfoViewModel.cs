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
    public partial class MyInfoViewModel : ObservableObject
    {
        private readonly UserSession _session;
        private readonly UserManager _manager;

        public MyInfoViewModel(UserSession session, UserManager manager) { 
            
            _session = session;
            _manager = manager;

        }

        // 팝업 표시/숨김
        [ObservableProperty] private bool isPwPopupVisible;
        [ObservableProperty] private bool hasPassword;


        // 내정보 기본 속성
        [ObservableProperty] private string company = "";
        [ObservableProperty] private string position = "";
        [ObservableProperty] private string name = "";
        [ObservableProperty] private string phoneNumber = "";
        [ObservableProperty] private string id = "";

        // 팝업창 속성
        [ObservableProperty] private string currentPw = "";
        [ObservableProperty] private string newPw = "";
        [ObservableProperty] private string confirmPw = "";

        [RelayCommand]
        public async Task LoadAsync()
        {
            var info = await _manager.GetUserInfoAsync();
            if (info == null)
            {
                return;
            }

            Company = info.CompanyName;
            Position = info.GradeName;   
            Name = _session.GetName();   
            PhoneNumber = info.PhoneNumber;
            Id = info.Id;
            HasPassword = info.HasPassword;
        }

        [RelayCommand]
        public void OpenChangePassword()
        {
            IsPwPopupVisible = true;
        }

        [RelayCommand]
        public void ClosePwPopup()
        {
            IsPwPopupVisible = false;
        }

        [RelayCommand(CanExecute = nameof(CanSavePassword))]
        private async Task SavePasswordAsync()
        {
            
            // TODO: 서버 호출 modify_user_info (current_pw + pw)
            // 성공 시 팝업 닫기 & 필드 초기화
        }

        [RelayCommand]
        public void Logout()
        {
            if(MessageBox.Show("로그아웃 하시겠습니까", "로그아웃", MessageBoxButton.YesNo, MessageBoxImage.Question) == MessageBoxResult.Yes)
            {
                WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Login));
            }
            
        }

        [RelayCommand]
        public void GoBack()
        {
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Goback));
        }


        public bool CanSavePassword =>
        !string.IsNullOrWhiteSpace(CurrentPw) &&
        !string.IsNullOrWhiteSpace(NewPw) &&
        NewPw == ConfirmPw &&
        NewPw.Length >= 8;
        public string PasswordMask => HasPassword ? "********" : "미설정";

        // HasPassword가 바뀔 때 Mask도 갱신 알림
        partial void OnHasPasswordChanged(bool value)
        {
            OnPropertyChanged(nameof(PasswordMask));
        }

        partial void OnCurrentPwChanged(string value)
        {
            OnPropertyChanged(nameof(CanSavePassword));
            SavePasswordCommand?.NotifyCanExecuteChanged();
        }
        partial void OnNewPwChanged(string value)
        {
            OnPropertyChanged(nameof(CanSavePassword));
            SavePasswordCommand?.NotifyCanExecuteChanged();
        }
        partial void OnConfirmPwChanged(string value)
        {
            OnPropertyChanged(nameof(CanSavePassword));
            SavePasswordCommand?.NotifyCanExecuteChanged();
        }
    }
}
