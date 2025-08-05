using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using Shifter.Messages;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Shifter.Enums;

namespace Shifter.ViewModels {
    public partial class MngEmpStartViewModel : ObservableObject {



        /** Constructor **/
        public MngEmpStartViewModel(Session? session) {
            _session = session;
        }



        /** Member Variables **/
        private readonly Session? _session;



        /** Member Methods **/
        /* Go To Register Employee Work(Shift) */
        [RelayCommand] private void GoToRgsEmpWork() {
            Console.WriteLine("[MngEmpStartViewModel] Executed GoToEmpsWork()");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.RgsEmpWork));
        }

        /* Go To Managing Employee */
        [RelayCommand] private void GoToMngEmp() {
            Console.WriteLine("MngEmpStartViewModel] GoToMngEmp()");
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.MngEmp));
        }
    }
}
