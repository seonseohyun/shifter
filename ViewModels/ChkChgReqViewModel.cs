using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Shifter.ViewModels {
    public partial class ChkChgReqViewModel : ObservableObject {

        /** Constructor **/
        public ChkChgReqViewModel(Session? session) {
            _session = session;

            YearMonth = DateTime.Now.ToString("yyyy-MM");
        }



        /** Member Variables **/
        private readonly Session? _session;
        private int _currentYear = (int)DateTime.Now.Year;
        private int _currentMonth = (int)DateTime.Now.Month;
        [ObservableProperty] private string? yearMonth;



        /** Member Methods **/
        [RelayCommand] void MinusMonth() {
            if (_currentMonth == 1) {
                _currentYear--;
                _currentMonth = 12;
            } else {
                _currentMonth--;
            }
            YearMonth = $"{_currentYear:D4}-{_currentMonth:D2}";
        }

        [RelayCommand] void PlusMonth() {
            if (_currentMonth == 12) {
                _currentYear++;
                _currentMonth = 1;
            } else {
                _currentMonth++;
            }
            YearMonth = $"{_currentYear:D4}-{_currentMonth:D2}";
        }
    }
}
