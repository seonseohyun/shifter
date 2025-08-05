using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Shifter.ViewModels {
    public partial class GenScdViewModel {

        /** Constructor **/
        public GenScdViewModel(Session? session) {
            _session = session;
        }



        /** Member Variables **/
        private readonly Session? _session;
        //[ObservableProperty] IList<team> teams;



        /** Member Methods **/
        [RelayCommand] void GenScd() {
            Console.WriteLine("[GenScdViewModel] Executed GenScd()");
        }
    }
}
