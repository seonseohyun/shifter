using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Shifter.ViewModels {
    public partial class GenScdViewModel : ObservableObject {

        /** Constructor **/
        public GenScdViewModel(Session? session) {
            _session = session;
        }



        /** Member Variables **/
        private readonly Session? _session;
        [ObservableProperty] private int? year  = DateTime.Now.Year;
        [ObservableProperty] private int? month = DateTime.Now.Month;



        /** Member Methods **/
        [RelayCommand] void GenScd() {
            Console.WriteLine("[GenScdViewModel] Executed GenScd()");
        }

        [RelayCommand] void MinusYear() {
            Console.WriteLine("[GenScdViewModel] Executed MinusYear()");
            Year--;
        }

        [RelayCommand] void MinusMonth() {
            Console.WriteLine("[GenScdViewModel] Executed MinusMonth()");
            if( Month > 1 ) {
                Month--;
            }
        }

        [RelayCommand] void PlusYear() {
            Console.WriteLine("[GenScdViewModel] Executed PlusYear()");    
            Year++;
        }

        [RelayCommand] void PlusMonth() {
            Console.WriteLine("[GenScdViewModel] Executed PlusMonth()");
            if( Month < 12 ) {
                Month++;
            }
        }
    }
}
