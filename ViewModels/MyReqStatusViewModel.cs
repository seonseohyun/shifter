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
using System.Threading.Tasks;

namespace ShifterUser.ViewModels
{
    public partial class MyReqStatusViewModel : ObservableObject
    {
        private readonly WorkRequestManager _reqModel;
        private readonly UserSession _session;
        private readonly int _uid;

        private bool suppressEvent = false;

        public IRelayCommand LoadOnAppearCommand { get; }
        public IAsyncRelayCommand LoadRequestsCommand { get; }

        public ObservableCollection<int> Years { get; } = new() { 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 };
        public ObservableCollection<int> Months { get; } = new() { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 };

        [ObservableProperty] private int selectedYear;
        [ObservableProperty] private int selectedMonth;
        [ObservableProperty] private WorkRequestStatus? filterStatus;
        [ObservableProperty] private bool isDetailVisible;


        private List<WorkRequestModel> allRequests = new();

        public ObservableCollection<WorkRequestModel> Requests { get; } = new();
        [ObservableProperty] private WorkRequestModel? selectedRequest;

        public MyReqStatusViewModel(WorkRequestManager manager, UserSession session)
        {
            _reqModel = manager;
            _session = session;
            _uid = session.GetUid(); // UID 저장

            LoadRequestsCommand = new AsyncRelayCommand(LoadRequestsAsync);
            LoadOnAppearCommand = new RelayCommand(LoadInitialData);

            // 이벤트 차단 후 초기 설정
            suppressEvent = true;
            SelectedYear = DateTime.Now.Year;
            SelectedMonth = DateTime.Now.Month;
            FilterStatus = null;
            suppressEvent = false;
        }


        private void LoadInitialData()
        {
            if (LoadRequestsCommand.CanExecute(null))
                LoadRequestsCommand.Execute(null);
        }

        private async Task LoadRequestsAsync()
        {
            allRequests = await _reqModel.LoadMonthRequestsAsync(_uid, SelectedYear, SelectedMonth);
            UpdateFilteredList();
        }

        private void UpdateFilteredList()
        {
            Requests.Clear();

            var filtered = allRequests
                .Where(r => FilterStatus == null || r.Status == FilterStatus)
                .ToList();

            foreach (var item in filtered)
                Requests.Add(item);
        }

        partial void OnSelectedYearChanged(int oldValue, int newValue)
        {
            if (!suppressEvent && LoadRequestsCommand.CanExecute(null))
                LoadRequestsCommand.Execute(null);
        }

        partial void OnSelectedMonthChanged(int oldValue, int newValue)
        {
            if (!suppressEvent && LoadRequestsCommand.CanExecute(null))
                LoadRequestsCommand.Execute(null);
        }

        partial void OnFilterStatusChanged(WorkRequestStatus? oldValue, WorkRequestStatus? newValue)
        {
            UpdateFilteredList();
        }

        [RelayCommand]
        private void ShowRequestDetail(WorkRequestModel item)
        {
            SelectedRequest = item;
            IsDetailVisible = true;

        }

        [RelayCommand]
        private async Task CancelRequestAsync()
        {
            if (SelectedRequest == null)
                return;

            int requestUid = SelectedRequest.Uid;

            bool result = await _reqModel.CancelShiftRequestAsync(requestUid);

            if (result)
            {
                Console.WriteLine("들어옴!!!!!!");
                // 다시 요청 목록 불러오기
                await LoadRequestsAsync();
                IsDetailVisible = false;
            }
            else
            {
                // 실패 메시지 출력
                Console.WriteLine("근무 요청 취소 실패");
            }
        }

        [RelayCommand]
        private void CloseDetail()
        {
            IsDetailVisible = false;
        }


        [RelayCommand]  

        private void GoToReqSche()
        {
            Console.WriteLine("근무 희망 요청 화면으로 이동");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.ReqSche));
        }

        [RelayCommand]
        private static void GoBack()
        {
            Console.WriteLine("[MyScheViewModel] GoBack command executed.");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Home));
        }
    }
}
