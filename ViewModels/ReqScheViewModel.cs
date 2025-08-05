using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using ShifterUser.Models;
using System;
using System.Collections.ObjectModel;

namespace ShifterUser.ViewModels
{
    public partial class ReqScheViewModel : ObservableObject
    {
        // 요청 객체 (날짜, 타입, 사유 포함)
        [ObservableProperty]
        private WorkRequestModel request = new()
        {
            RequestDate = DateTime.Today,
            ShiftType = ShiftType.Day,
            Reason = ""
        };

        // 제목 바인딩용 (ex. 09월 근무 희망 일정 요청)
        [ObservableProperty]
        private string requestTitle = "";

        // 날짜 선택 목록 
        public ObservableCollection<DateTime> AvailableDates { get; } = new()
        {
            DateTime.Today,
            DateTime.Today.AddDays(1),
            DateTime.Today.AddDays(2)
        };

        // 교대 종류 선택 목록
        public ObservableCollection<ShiftType> ShiftTypes { get; } = new()
        {
            ShiftType.Day,
            ShiftType.Night,
            ShiftType.Off,
            ShiftType.Evening
        };

        // 바인딩용 프로퍼티들
        public DateTime SelectedDate
        {
            get => Request.RequestDate;
            set => Request.RequestDate = value;
        }

        public ShiftType SelectedShiftType
        {
            get => Request.ShiftType;
            set => Request.ShiftType = value;
        }

        public string Reason
        {
            get => Request.Reason;
            set => Request.Reason = value;
        }

        // 생성자
        public ReqScheViewModel()
        {
            RequestTitle = $"{DateTime.Now.AddMonths(1):MM}월 근무 희망 일정 요청";
        }

        // 등록 명령
        [RelayCommand]
        private void RegisterReq()
        {
            Console.WriteLine($"[등록됨] 날짜: {SelectedDate}, 타입: {SelectedShiftType}, 사유: {Reason}");
            // 서버 전송
        }

        // 뒤로가기 
        [RelayCommand]
        private void GoBack()
        {
            Console.WriteLine("뒤로 가기 실행됨");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Goback));
        }
    }
}
