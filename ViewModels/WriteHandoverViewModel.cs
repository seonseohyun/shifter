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
    public partial class WriteHandoverViewModel : ObservableObject
    {
        private readonly UserSession _session;
        public ObservableCollection<string> HandoverTypes { get; } = new()
        {
            "교대", "출장", "휴가/부재", "퇴사", "장비/물품", "기타"
        };

        // 생성자
        public WriteHandoverViewModel(UserSession session) {
            _session = session;
        }

        [RelayCommand]
        private void GoToHandover()
        {
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.HandoverPopup));
        }

        [RelayCommand]
        private void GoBack()
        {
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Goback));
        }

    }
}
