using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using Shifter.Enums;
using Shifter.Messages;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Media.Animation;

namespace Shifter.ViewModels {
    public partial class HomeViewModel : ObservableObject {

        /** Constructor **/
        public HomeViewModel(Session? session, ScdModel scdmodel) {
            _session = session!;
            _scdmodel = scdmodel;

            _session.VisGoBack = false;

            TeamName = _session.GetCurrentTeamName();
            //_ = _scdmodel!.ReqShiftInfo();

            _ = CheckTodayDuty();
        }



        /** Member Variables **/
        private readonly Session? _session;
        private readonly ScdModel? _scdmodel;
        [ObservableProperty] private string? teamName = "";
        [ObservableProperty] private string? dateOfToday = DateTime.Today.Date.ToString()[..10];
        [ObservableProperty] ObservableCollection<TodaysDutyInfo> todaysDuty = [];



        /** Member Methods **/
        /* Go to ChkChgReqView */
        [RelayCommand] void GoToChkChgReq() {
            _session!.VisGoBack = true;
            Console.WriteLine("[HomeViewModel] Executed GoToChkChgReq()");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.ChkChgReq));
        }

        /* Go to ChkChgReqView */
        [RelayCommand] void GoToStatus() {
            _session!.VisGoBack = true;
            Console.WriteLine("[HomeViewModel] Executed GoToStatus()");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.Status));
        }

        /* Check Today's Duty & Admit to UI */
        public async Task CheckTodayDuty() {
            Console.WriteLine("[HomeViewModel] Executed CheckTodayDuty()");

            var list = await _scdmodel!.CheckTodayDutyAsync(); // List<TodaysDutyInfo>
            Console.WriteLine("[HomeViewModel] TodaysDuty count: " + list.Count);
            TodaysDuty = new ObservableCollection<TodaysDutyInfo>(list);
        }
    }
}
