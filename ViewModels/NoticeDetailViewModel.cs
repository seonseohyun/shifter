using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Messages;
using ShifterUser.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ShifterUser.ViewModels
{
    public partial class NoticeDetailViewModel : ObservableObject
    {
        private readonly NoticeManager _notice;

        [ObservableProperty] private bool isLoading;
        [ObservableProperty] private NoticeModel? notice;

        public NoticeDetailViewModel(NoticeManager notice)
        {
            _notice = notice;

            // UID 수신 시 자동 로드
            WeakReferenceMessenger.Default.Register<OpenNoticeDetailMessage>(this,
                async (_, m) => await LoadAsync(m.Value));

            // 테스트용
            Notice = new NoticeModel { Title = "테스트", StaffName = "관리자", NoticeDate = "2025-08-08", Content = "하드코딩" };

        }


        partial void OnNoticeChanged(NoticeModel? value)
        {
            Console.WriteLine($"[VM] Notice set #{GetHashCode()} title={value?.Title}");
        }


        public async Task LoadAsync(int noticeUid)
        {
            try
            {
                IsLoading = true;
                Notice = await _notice.GetNoticeDetailAsync(noticeUid);
            }
            finally { IsLoading = false; }
        }

        [RelayCommand]
        private void GoBack()
        {
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(Enums.PageType.Goback));
        }

    }

}
