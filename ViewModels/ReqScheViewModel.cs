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
            _workRequestManager = workRequestManager;

            // 시작: 내일(오늘 + 1일)
            DateTime start = DateTime.Today.AddDays(1);

            // 끝: 다음 달 마지막 날
            int nextMonth = (start.Month == 12) ? 1 : start.Month + 1;
            int nextYear = (start.Month == 12) ? start.Year + 1 : start.Year;
            DateTime end = new DateTime(
                nextYear,
                nextMonth,
                DateTime.DaysInMonth(nextYear, nextMonth)
            );

            // 날짜 목록 초기화 후 채우기
            AvailableDates.Clear();
            for (DateTime d = start.Date; d <= end; d = d.AddDays(1))
                AvailableDates.Add(d);

            // 기본 선택 날짜: 내일
            SelectedDate = start.Date;

            // 제목: 범위 표시(예: "08~09월 근무 희망 일정 요청")
            string title =
                (start.Month == end.Month && start.Year == end.Year)
                ? $"{start:MM}월 근무 희망 일정 요청"
                : $"{start:MM}~{end:MM}월 근무 희망 일정 요청";
            RequestTitle = title;
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
