using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using Shifter.Enums;
using Shifter.Messages;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Shifter.ViewModels {
    public partial class MngScdViewModel : ObservableObject {

        /** Constructor **/
        public MngScdViewModel(Session? session, ScdModel scdModel) {
            _session = session;
            _scdModel = scdModel;

            /* Temp Values */
            CompanyName  = "Company Name";
            TeamName     = "Team Name";
            AdminName    = "Admin Name";

            /* Init Time */
            CurrentYear  = (int) DateTime.Now.Year;
            CurrentMonth = (int) DateTime.Now.Month;

            YearMonth = CurrentYear.ToString() + "년 " + CurrentMonth.ToString() + "월";

            /* Get Admin Time Table */
            _ = _scdModel.AskTimeTableAdminAsync(CurrentYear!.Value, CurrentMonth!.Value);
        }



        /** Member Variables **/
        private readonly Session? _session;
        private readonly ScdModel _scdModel;
        [ObservableProperty] private int? currentYear;
        [ObservableProperty] private int? currentMonth;
        [ObservableProperty] private string? yearMonth;
        [ObservableProperty] private string? companyName;
        [ObservableProperty] private string? teamName;
        [ObservableProperty] private string? adminName;



        /** Member Methods **/

        /* Go to Check Changes Requirement */
        [RelayCommand] void GoToChkChgReq() {
            Console.WriteLine("[MngScdViewModel] Executed GoToChkChgReq()");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.ChkChgReq));
        }

        /* Go to Modify Schedule */
        [RelayCommand] void GoToMdfScd() {
            Console.WriteLine("[MngScdViewModel] Executed GoToMdfScd()");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.MdfScd));
        }

        /* Minus Month Commnad */
        [RelayCommand] void MinusMonth() {
            Console.WriteLine("[MngScdViewModel] Executed MinusMonth()");
            if (CurrentMonth > 1) {
                CurrentMonth--;
            } else {
                CurrentYear--;
                CurrentMonth = 12;
            }
            YearMonth = CurrentYear.ToString() + "년 " + CurrentMonth.ToString() + "월";
            _ = _scdModel.AskTimeTableAdminAsync(CurrentYear!.Value, CurrentMonth!.Value);
        }

        /* Plus Month Command */
        [RelayCommand] void PlusMonth() {
            Console.WriteLine("[MngScdViewModel] Executed PlusMonth()");
            if (CurrentMonth < 12) {
                CurrentMonth++;
            } else {
                CurrentYear++;
                CurrentMonth = 1;
            }
            YearMonth = CurrentYear.ToString() + "년 " + CurrentMonth.ToString() + "월";
            _ = _scdModel.AskTimeTableAdminAsync(CurrentYear!.Value, CurrentMonth!.Value);
        }
    }
}
