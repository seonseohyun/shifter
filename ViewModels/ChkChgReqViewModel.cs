using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using static Shifter.Models.ScdModel;



namespace Shifter.ViewModels {
    public partial class ChkChgReqViewModel : ObservableObject {

        private readonly ScdModel _sm;
        private bool _loaded;
        /** Constructor **/
        public ChkChgReqViewModel(Session? session, ScdModel sm) {
            _session = session;
            _sm = sm;

            YearMonth = DateTime.Now.ToString("yyyy-MM");

            LoadOnAppearAsyncCommand = new AsyncRelayCommand(LoadOnAppearAsync);

        }

        public IAsyncRelayCommand LoadOnAppearAsyncCommand { get; }

        private async Task LoadOnAppearAsync()
        {
            Console.WriteLine("LoadOnAppearAsync() 호출됨");

            if (_loaded) return; 
            _loaded = true;

            Scr = await _sm.ShiftChangeList(_currentYear, _currentMonth);
         
        }

        /** Member Variables **/
        private readonly Session? _session;
        private int _currentYear = (int)DateTime.Now.Year;
        private int _currentMonth = (int)DateTime.Now.Month;

        [ObservableProperty] private string? yearMonth;
        [ObservableProperty] private ObservableCollection<ShiftChangeRequestInfo> scr;
        [ObservableProperty] private string? rejectReason = "";
        [ObservableProperty] private ShiftChangeRequestInfo? selectedRequest;
        [ObservableProperty] private bool isWriteVisible;



        [RelayCommand]
        void OpenWriteRejectReason(ShiftChangeRequestInfo item)
        {
            SelectedRequest = item;
            IsWriteVisible = true;
        }

        [RelayCommand]
        async Task Approve(ShiftChangeRequestInfo item)
        {
            if (!string.Equals(item.Status, "pending", StringComparison.OrdinalIgnoreCase))
            {
                Console.WriteLine(item.Status == "approved" ? "이미 승인된 요청입니다." : "이미 반려된 요청입니다.");
                return;
            }

            var (ok, msg) = await _sm.AnswerShiftChangeAsync(
                dutyRequestUid: item.DutyRequestUid,
                status: "approved",
                date: item.RequestDate,
                dutyType: item.DesireShift,     
                adminMsg: ""                
            );

            if (ok)
                Scr = await _sm.ShiftChangeList(_currentYear, _currentMonth);
            else
                Console.WriteLine($"approve failed: {msg}");
        }

        [RelayCommand]
        async Task Reject()
        {
            if (SelectedRequest is null) return;
            if (!string.Equals(SelectedRequest.Status, "pending", StringComparison.OrdinalIgnoreCase))
            {
                Console.WriteLine(SelectedRequest.Status == "approved" ? "이미 승인된 요청입니다." : "이미 반려된 요청입니다.");
                return;
            }

            var (ok, msg) = await _sm.AnswerShiftChangeAsync(
                dutyRequestUid: SelectedRequest.DutyRequestUid,
                status: "rejected",
                date: SelectedRequest.RequestDate,
                dutyType: SelectedRequest.DesireShift,
                adminMsg: RejectReason ?? ""
            );

            if (ok)
            {
                IsWriteVisible = false;
                RejectReason = "";
                Scr = await _sm.ShiftChangeList(_currentYear, _currentMonth);
            }
            else
            {
                Console.WriteLine($"reject failed: {msg}");
            }
        }


        [RelayCommand] void ClosePopup()
        {
            IsWriteVisible = false;
        }

        [RelayCommand]
        private async Task MinusMonth()
        {
            if (_currentMonth == 1)
            {
                _currentYear--;
                _currentMonth = 12;
            }
            else
            {
                _currentMonth--;
            }

            YearMonth = $"{_currentYear:D4}-{_currentMonth:D2}";
            Scr = await _sm.ShiftChangeList(_currentYear, _currentMonth);
        }

        [RelayCommand]
        private async Task PlusMonth()
        {
            if (_currentMonth == 12)
            {
                _currentYear++;
                _currentMonth = 1;
            }
            else
            {
                _currentMonth++;
            }

            YearMonth = $"{_currentYear:D4}-{_currentMonth:D2}";
            Scr = await _sm.ShiftChangeList(_currentYear, _currentMonth);
        }

    }
}
