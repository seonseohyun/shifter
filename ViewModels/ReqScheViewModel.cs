using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using ShifterUser.Enums;
using ShifterUser.Messages;
using ShifterUser.Models;
using System;
using System.Collections.ObjectModel;
using System.Drawing;
using System.Windows;
using static System.Runtime.InteropServices.JavaScript.JSType;

namespace ShifterUser.ViewModels
{
    public partial class ReqScheViewModel : ObservableObject
    {
        [ObservableProperty]
        private WorkRequestModel request = new()
        {
            RequestDate = DateTime.Today,
            ShiftType = ShiftType.Day,
            Reason = ""
        };
        private readonly WorkRequestManager _workRequestManager;
        [ObservableProperty]
        private string requestTitle = "";

        public ObservableCollection<DateTime> AvailableDates { get; } = new();

        public ObservableCollection<ShiftType> ShiftTypes { get; } = new()
    {
        ShiftType.Day,
        ShiftType.Night,
        ShiftType.Off,
        ShiftType.Evening
    };

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

        public ReqScheViewModel(WorkRequestManager workRequestManager)
        {
            // 다음 달 계산
            DateTime now = DateTime.Now;
            int nextMonth = now.Month == 12 ? 1 : now.Month + 1;
            int nextYear = now.Month == 12 ? now.Year + 1 : now.Year;

            int daysInNextMonth = DateTime.DaysInMonth(nextYear, nextMonth);
            for (int day = 1; day <= daysInNextMonth; day++)
            {
                AvailableDates.Add(new DateTime(nextYear, nextMonth, day));
            }

            // 기본 선택 날짜: 다음 달 1일
            SelectedDate = new DateTime(nextYear, nextMonth, 1);

            // 제목 설정
            RequestTitle = $"{nextMonth:00}월 근무 희망 일정 요청";
            _workRequestManager = workRequestManager;
        }

        [RelayCommand]
        private void RegisterReq()
        {
            Console.WriteLine($"[등록됨] 날짜: {SelectedDate}, 타입: {SelectedShiftType}, 사유: {Reason}");

            bool success = _workRequestManager.SendRequest(SelectedDate, SelectedShiftType, Reason);

            if (success)
            {
                Console.WriteLine("요청 성공");
                //WeakReferenceMessenger.Default.Send(new RequestUpdatedMessage());
                MessageBox.Show("요청이 전송되었습니다!");
                GoBack(); // 혹은 메시지 전송
            }
            else
            {
                Console.WriteLine("요청 실패");
            }
        }

        [RelayCommand]
        private void GoBack()
        {
            Console.WriteLine("뒤로 가기 실행됨");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Goback));
        }
    }

}
