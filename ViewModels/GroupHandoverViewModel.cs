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
    public partial class GroupHandoverViewModel : ObservableObject
    {
        private readonly UserSession _session;
        private readonly HandoverManager _manager;
        private readonly SocketManager _socket;

        private List<HandoverModel> allHandovers = new();

        [ObservableProperty] private string teamName;
        [ObservableProperty] private string selectedHandoverType = "전체";
        [ObservableProperty] private bool isDetailVisible;
        [ObservableProperty] private HandoverModel? selectedHandover;
        [ObservableProperty] private HandoverDetailModel? selectedHandoverDetail;

        public ObservableCollection<string> HandoverTypes { get; } = new()
        {
            "전체", "교대", "출장", "휴가/부재", "퇴사", "장비/물품", "기타"
        };

        public ObservableCollection<HandoverModel> HandoverList { get; } = new();


        public IAsyncRelayCommand LoadOnAppearAsyncCommand { get; }

        public GroupHandoverViewModel(SocketManager socket, UserSession session)
        {
            Console.WriteLine("GroupHandoverViewModel 생성자 호출됨");

            _session = session;
            _socket = socket;
            _manager = new HandoverManager(socket, session);

            TeamName = _session.GetTeamName();
            LoadOnAppearAsyncCommand = new AsyncRelayCommand(LoadOnAppearAsync);
        }

        private async Task LoadOnAppearAsync()
        {
            Console.WriteLine("LoadOnAppearAsync() 호출됨");

            try
            {
                allHandovers = _manager.LoadHandoverList();

                Console.WriteLine($"[디버그] 전체 인수인계 수신 개수: {allHandovers.Count}");

                // 강제로 필터 초기화 트리거
                SelectedHandoverType = "전체";
                UpdateFilteredList();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[에러] 인수인계 목록 불러오기 실패: {ex.Message}");
                allHandovers.Clear();
                HandoverList.Clear();
            }
        }
        private void UpdateFilteredList()
        {
            HandoverList.Clear();

            Console.WriteLine("====== 필터링 시작 ======");
            Console.WriteLine($" 현재 선택된 필터: {SelectedHandoverType}");

            List<HandoverModel> filtered = new();

            foreach (var item in allHandovers)
            {
                string converted = GetDisplayName(item.ShiftTypeTag);
                Console.WriteLine($"→ 항목: {item.Title}, note_type={item.ShiftTypeTag}, 변환된 문자열={converted}");

                if (SelectedHandoverType == "전체" || converted == SelectedHandoverType)
                    filtered.Add(item);
            }

            foreach (var h in filtered)
            {
                Console.WriteLine($" 추가됨: {h.Title} / {GetDisplayName(h.ShiftTypeTag)}");
                HandoverList.Add(h);
            }

            Console.WriteLine($" 최종 추가된 인수인계 수: {HandoverList.Count}");
            Console.WriteLine("====== 필터링 종료 ======");
        }

        [RelayCommand]
        private void ShowHandoverDetail(HandoverModel item)
        {
            // 먼저 페이지 전환
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.HandoverDetail));
            WeakReferenceMessenger.Default.Send(new HandoverDetailRequestMessage(item.HandoverUid));
 
        }

        // Enum → 사용자 표시 문자열로 변환
        private string GetDisplayName(HandoverType type) => type switch
        {
            HandoverType.교대 => "교대",
            HandoverType.출장 => "출장",
            HandoverType.휴가및부재 => "휴가/부재",
            HandoverType.퇴사 => "퇴사",
            HandoverType.장비및물품 => "장비/물품",
            HandoverType.기타 => "기타",
            _ => "기타"
        };

        partial void OnSelectedHandoverTypeChanged(string oldValue, string newValue)
        {
            UpdateFilteredList();
        }


        [RelayCommand]
        private void CloseDetail()
        {
            IsDetailVisible = false;
        }

        [RelayCommand]
        private void GoToWriteHandover()
        {
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.WriteHandover));
        }

        [RelayCommand]
        private void GoBack()
        {
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Goback));
        }
    }
}
