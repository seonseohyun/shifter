using CommunityToolkit.Mvvm.ComponentModel;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Shifter.ViewModels {
    public partial class MngEmpViewModel : ObservableObject {

        /** Constructor **/
        public MngEmpViewModel(Session? session) {
            _session = session;
        }



        /** Member Variables **/
        private readonly Session? _session;



        /** Member Methods **/
    }
}
