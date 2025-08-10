using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using ShifterUser.Models;
using ShifterUser.Services;  
using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;

namespace ShifterUser.ViewModels
{
    public partial class GroupDashboardViewModel : ObservableObject
    {
        // 콤보박스
        public ObservableCollection<string> Teams { get; } = new();
        [ObservableProperty] private string? selectedTeam;

        // 오늘 근무 현황
        public ObservableCollection<TodayDutyGroup> TodayGroups { get; } = new();

        // 화면 텍스트
        [ObservableProperty] private string teamName = "";
        [ObservableProperty] private string topTeamName = "";

        // 상태
        [ObservableProperty] private bool isBusy;
        [ObservableProperty] private string? errorMessage;

        private readonly UserSession _session;
        private readonly TimetableManager _timetable;

        public GroupDashboardViewModel(UserSession session, TimetableManager timetable)
        {
            _session = session;
            _timetable = timetable;

            var currentTeam = _session.GetTeamName();
            TopTeamName = currentTeam ?? "";

            Teams.Clear();
            if (!string.IsNullOrWhiteSpace(currentTeam))
                Teams.Add(currentTeam);

            SelectedTeam = Teams.FirstOrDefault();
            TeamName = SelectedTeam ?? "";
        }

        // 바인딩 아이템
        public class TodayDutyGroup
        {
            
            public string Shift { get; set; } = "";
            public ObservableCollection<string> Staff { get; } = new();
        }

        // 네비게이션 
        [RelayCommand] private static void GoBack() => WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Goback));
        [RelayCommand] private static void GoToHandover() => WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.GroupHandover));
        [RelayCommand] private static void GoToNotice() => WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.GroupNotice));

        // 초기 로딩 & 새로고침 
        [RelayCommand]
        public async Task InitializeAsync()
        {
            await LoadTodayAsync(DateTime.Now);
        }

        [RelayCommand]
        public async Task RefreshAsync()
        {
            await LoadTodayAsync(DateTime.Now);
        }

        // 팀 선택 바뀌면 자동 재로딩
        partial void OnSelectedTeamChanged(string? value)
        {
            _ = LoadTodayAsync(DateTime.Now);
        }

        // 서버에서 받아서 TodayGroups 채우기 
        private async Task LoadTodayAsync(DateTime date)
        {


            int teamUid = _session.GetTeamCode();
            var dtoList = await _timetable.GetTodayDutyAsync(date, teamUid);

            TodayGroups.Clear();

            foreach (var dto in dtoList)
            {
                // staff 없는 섹션은 미노출
                if (dto.Staff == null || dto.Staff.Count == 0) continue;

                var vmItem = new TodayDutyGroup { Shift = dto.Shift };
                foreach (var name in dto.Staff)
                {
                    if (!string.IsNullOrWhiteSpace(name))
                        vmItem.Staff.Add(name);
                }
                TodayGroups.Add(vmItem);
            }
        }

    }
}
