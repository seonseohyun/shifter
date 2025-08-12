using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using ShifterUser.Models;
using System;
using System.Collections.ObjectModel;
using System.Windows;
using System.Windows.Media;


namespace ShifterUser.ViewModels
{
    public partial class HomeViewModel : ObservableObject
    {
        private readonly UserSession _session;
        private readonly UserManager _manager;
        public ObservableCollection<string> WeeklyCodes { get; } =
        new ObservableCollection<string>(new[] { "-", "-", "-", "-", "-", "-", "-" });
        public void Receive(AttendanceChangedMessage m) => RefreshAttendanceFromSession();

        public void RefreshAttendanceFromSession() 
        {
            var att = _session.GetAttendance();
            if (att?.ClockOutTime != null) AttendanceStatus = AttendanceStatus.퇴근완료;
            else if (att?.ClockInTime != null) AttendanceStatus = AttendanceStatus.출근완료;
            else AttendanceStatus = AttendanceStatus.출근전;
        }


        // 바인딩 속성
        [ObservableProperty] private string todayDate;
        [ObservableProperty] private string teamName;
        [ObservableProperty] private string approvedText;
        [ObservableProperty] private string pendingText;
        [ObservableProperty] private string rejectedText;
        [ObservableProperty]
        [NotifyPropertyChangedFor(nameof(AttendanceText))]
        private AttendanceStatus attendanceStatus = AttendanceStatus.출근전;
        [ObservableProperty] private Brush attendanceColor = Brushes.Gray;

        public HomeViewModel(UserSession session, UserManager userManager)
        {
            _session = session;
            _manager = userManager;
            _ = LoadWeekAsync(DateTime.Today);
            WeakReferenceMessenger.Default.RegisterAll(this);

            // 최초 진입 시 세션 기준으로 1회 반영
            RefreshAttendanceFromSession();

            // 초기화
            TeamName = _session.GetTeamName();
            TodayDate = _session.GetDate();

            var (approved, pending, rejected) = _session.GetRequestStatus();
            ApprovedText = $" 승인 {approved}건";
            PendingText = $" 대기 {pending}건";
            RejectedText = $" 반려 {rejected}건";

            var att = _session.GetAttendance();
            if (att != null)
            {
                if (att.ClockOutTime != null)
                    AttendanceStatus = AttendanceStatus.퇴근완료;
                else if (att.ClockInTime != null)
                    AttendanceStatus = AttendanceStatus.출근완료;
                else
                    AttendanceStatus = AttendanceStatus.출근전;
            }

            WeakReferenceMessenger.Default.Register<HomeViewModel, AttendanceChangedMessage>(
            this, (r, m) => r.RefreshAttendanceFromSession());

            WeakReferenceMessenger.Default.Register<HomeViewModel, WorkWishSubmittedMessage>(
                this, async (r, m) => await r.ReloadAllAsync());

        }



        public async Task ReloadAllAsync()
        {
            await LoadWeekAsync(DateTime.Today);

            // 출퇴근은 세션 기준 즉시 반영
            RefreshAttendanceFromSession();

            // 요청 현황 텍스트 갱신 (세션이 갱신되어 있다면 그대로, 아니라면 여기서 서버 재조회 메서드 호출)
            var (approved, pending, rejected) = _session.GetRequestStatus();
            ApprovedText = $" 승인 {approved}건";
            PendingText = $" 대기 {pending}건";
            RejectedText = $" 반려 {rejected}건";
        }

        partial void OnAttendanceStatusChanged(AttendanceStatus oldValue, AttendanceStatus newValue)
        {
            AttendanceColor = newValue switch
            {
                AttendanceStatus.출근완료 => System.Windows.Media.Brushes.Green,
                AttendanceStatus.퇴근완료 => System.Windows.Media.Brushes.Blue,
                _ => System.Windows.Media.Brushes.Gray
            };
        }


        private async Task LoadWeekAsync(DateTime any)
        {
            int offset = ((int)any.DayOfWeek + 6) % 7; // Mon=0
            var monday = any.Date.AddDays(-offset);

            var codes = await _manager.GetWeeklyShiftCodesAsync(monday); 
            for (int i = 0; i < 7; i++)
                WeeklyCodes[i] = (codes[i] ?? "-").ToUpperInvariant();
        }


        public string AttendanceText => AttendanceStatus switch
        {
            AttendanceStatus.출근완료 => "출근 완료",
            AttendanceStatus.퇴근완료 => "퇴근 완료",
            AttendanceStatus.출근전 => "출근 전입니다",
            _ => string.Empty
        };

        public void UpdateAttendanceStatusFromMessage(string message)
        {
            AttendanceStatus = message switch
            {
                        "출근 완료" => AttendanceStatus.출근완료,
                        "퇴근 완료" => AttendanceStatus.퇴근완료,
                        _ => AttendanceStatus.출근전
            };
        }

        // 페이지 이동 커맨드
        [RelayCommand]
        private void OpenMyInfo()
        {
            Console.WriteLine("내정보 페이지로 이동합니다.");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.MyInfo));
        }

        [RelayCommand]
        private void GoToQrCheck()
        {
            Console.WriteLine("QR 페이지로 이동합니다.");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.QR));
        }
            

        [RelayCommand]
        private void GoToGroupActivity()
        {
            Console.WriteLine("그룹 페이지로 이동합니다.");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.GroupDashboard));
        }

        [RelayCommand]
        private void GoToNotice()
        {
            Console.WriteLine("공지사항 페이지로 이동합니다.");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.GroupNotice));
        }

        [RelayCommand]
        private void GoToHandover()
        {
            Console.WriteLine("인수인계 페이지로 이동합니다.");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.GroupHandover));
        }

        [RelayCommand]
        private void GoToSchedule()
        {
            Console.WriteLine("스케줄 페이지로 이동합니다.");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.MySche));
        }

        [RelayCommand]
        private void GoToRequestStatus()
        {
            Console.WriteLine("근무 요청 페이지로 이동합니다.");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.ReqStatus));
        }
    }
}
