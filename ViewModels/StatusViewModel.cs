using CommunityToolkit.Mvvm.ComponentModel;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Shifter.Models;

namespace Shifter.ViewModels {
    public partial class StatusViewModel : ObservableObject {

        /** Constructor **/
        public StatusViewModel(Session? session) {
            _session = session;
        }


        /** Member Variables **/
        private readonly Session? _session;
        /** Member Methods **/
    }
}
