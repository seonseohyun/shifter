using CommunityToolkit.Mvvm.ComponentModel;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Shifter.ViewModels {
    public partial class ChkTmpEmpViewModel : ObservableObject {

        /** Constructor **/
        public ChkTmpEmpViewModel(Session? session) {
            _session = session;
        }



        /** Member Variables **/
        private readonly Session? _session;



        /** Member Methods **/
    }
}