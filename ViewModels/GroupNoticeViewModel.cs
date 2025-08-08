using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using ShifterUser.Models;
using ShifterUser.Services;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;

namespace ShifterUser.ViewModels
{
    public partial class GroupNoticeViewModel : ObservableObject
    {
        private readonly NoticeManager _notice;
        private readonly UserSession _session;

        public GroupNoticeViewModel(NoticeManager notice, UserSession session)
        {
            _notice = notice;
            _session = session;
            TeamName = session.GetTeamName();
            LoadOnAppearAsyncCommand = new AsyncRelayCommand(LoadOnAppearAsync);
            OpenDetailCommand = new RelayCommand<NoticeModel>(OpenDetail);
            GoBackCommand = new RelayCommand(GoBack);
        }

        public ObservableCollection<NoticeModel> Notices { get; } = new();

        [ObservableProperty] private string teamName = "";
        [ObservableProperty] private bool isBusy;

        public IAsyncRelayCommand LoadOnAppearAsyncCommand { get; }
        public IRelayCommand<NoticeModel> OpenDetailCommand { get; }
        public IRelayCommand GoBackCommand { get; }

        private async Task LoadOnAppearAsync()
        {
            if (IsBusy) return;
            IsBusy = true;
            try
            {
                var list = await Task.Run(() => _notice.LoadNoticeList());
                Notices.Clear();
                foreach (var n in list) Notices.Add(n);
            }
            finally { IsBusy = false; }
        }

        private void OpenDetail(NoticeModel? item)
        {
            if (item is null) return;
            // TODO: 상세 페이지로 이동(ask_notice_detail) or 팝업
        }

        private void GoBack()
        {
           WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Goback));
        }
    }


}
