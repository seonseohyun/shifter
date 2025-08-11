using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using static Shifter.Models.ScdModel;



namespace Shifter.ViewModels {
    public partial class ChkChgReqViewModel : ObservableObject {

        

        private readonly ScdModel _sm;
        /** Constructor **/
        public ChkChgReqViewModel(Session? session, ScdModel sm) {
            _session = session;
            _sm = sm;

            YearMonth = DateTime.Now.ToString("yyyy-MM");

            LoadOnAppearAsyncCommand = new AsyncRelayCommand(LoadOnAppearAsync);

        }

        public IAsyncRelayCommand LoadOnAppearAsyncCommand { get; }

        private async Task LoadOnAppearAsync()
        {
            Console.WriteLine("LoadOnAppearAsync() 호출됨");

            Scr = await _sm.ShiftChangeList(_currentYear, _currentMonth);
         
        }

        /** Member Variables **/
        private readonly Session? _session;
        private int _currentYear = (int)DateTime.Now.Year;
        private int _currentMonth = (int)DateTime.Now.Month;

        [ObservableProperty] private string? yearMonth;
        [ObservableProperty] private ObservableCollection<ShiftChangeRequestInfo> scr;



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
