using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using ShifterUser.Models;
using ShifterUser.Services;
using System;
using System.Threading.Tasks;

namespace ShifterUser.ViewModels
{
    public partial class HandoverPopupViewModel : ObservableObject
    {
        private readonly UserSession _session;
        private readonly HandoverManager _handover;

        [ObservableProperty] private int handoverUid;          // 받은 uid 저장
        [ObservableProperty] private string author = "";
        [ObservableProperty] private DateTime registerDate;    // 화면에 yyyy.MM.dd로 포맷 바인딩
        [ObservableProperty] private string teamName = "";


        public HandoverPopupViewModel(UserSession session, HandoverManager handover)
        {
            _session = session;
            _handover = handover;

            Author = _session.GetName();
            RegisterDate = DateTime.Today;
            Console.WriteLine($"Check Date : {DateTime.Now}");
            Console.WriteLine($"Check Data : {DateTime.Today}");
            // 기본값
            TeamName = _session.GetTeamName() ?? "";

            // 등록 완료 메시지 수신 → uid 저장 → 상세 로드
            WeakReferenceMessenger.Default.Register<HandoverRegisteredMessage>(this, async (r, m) =>
            {
                HandoverUid = m.HandoverUid;
            });
        }

        // 확인
        [RelayCommand]
        private void Confirm()
        {
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.GroupHandover));
        }

        // 바로 보기
        [RelayCommand]
        private void ViewNow()
        {
            WeakReferenceMessenger.Default.Send(new OpenHandoverDetailMessage(HandoverUid));
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.HandoverDetail));
        }
    }
}
