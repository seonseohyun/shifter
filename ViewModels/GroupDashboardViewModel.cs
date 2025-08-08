using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using ShifterUser.Models;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ShifterUser.ViewModels
{
    public partial class GroupDashboardViewModel : ObservableObject
    {
        // 콤보박스에 바인딩할 컬렉션
        public ObservableCollection<string> Teams { get; } = new();

        // 선택값(양방향 바인딩 대상)
        [ObservableProperty] private string? selectedTeam;

        // 기존 보여줄 텍스트들
        [ObservableProperty] private string teamName = "";
        [ObservableProperty] private string topTeamName = "";

        private readonly UserSession _session;

        public GroupDashboardViewModel(UserSession session)
        {
            _session = session;

            var currentTeam = _session.GetTeamName();
            TopTeamName = currentTeam ?? "";

            Teams.Clear();
            if (!string.IsNullOrWhiteSpace(currentTeam))
                Teams.Add(currentTeam);   

            SelectedTeam = Teams.FirstOrDefault();
            TeamName = SelectedTeam ?? "";
        }




        [RelayCommand]
        private static void GoBack()
        {
            WeakReferenceMessenger.Default.Send((new PageChangeMessage(PageType.Goback)));
        }

        [RelayCommand]
        private static void GoToHandover()
        {
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.GroupHandover));
        }

        [RelayCommand]
        private static void GoToNotice()
        {
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.GroupNotice));
        }
    }
}