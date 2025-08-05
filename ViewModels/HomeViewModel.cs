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
using System.Windows.Media.Animation;

namespace Shifter.ViewModels {
    public partial class HomeViewModel : ObservableObject {

        /** Constructor **/
        public HomeViewModel(Session? session) {
            _session = session!;

            _session.VisGoBack = false;
        }



        /** Member Variables **/
        private readonly Session? _session;



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
    }
}
