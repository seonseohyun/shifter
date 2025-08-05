using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using Shifter.Messages;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;

namespace Shifter.ViewModels {
    public partial class RgsEmpWorkViewModel : ObservableObject {
        /** Constructor **/
        public RgsEmpWorkViewModel(Session? session) {
            _session = session;
        }



        /** Member Variables **/
        private readonly Session? _session;
        [ObservableProperty] private ObservableCollection<ShiftItem> shifts = new();
        [ObservableProperty] private string? selectedIndustry;



        /** Member Methods **/
        [RelayCommand] private void AddShift() {
            if( Shifts.Count < 5 ) {
                Shifts.Add(new ShiftItem {
                    ShiftType = "",
                    StartTime = "00:00",
                    EndTime = "00:00"
                });
            }
            else if( Shifts.Count == 5 ) {
                MessageBox.Show("근무정보는 최대 다섯개(휴무포함)까지 추가가능합니다.", "Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }


        /* Select Industry( Change Button Colors ) */
        [RelayCommand] private void SelectIndustry(string industry) {
            SelectedIndustry = industry;
        }


        /* Go To Register Employee Grade */
        [RelayCommand] private void GoToRgsEmpGrade() {
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(Enums.PageType.RgsEmpGrade));
        }
    }


    public partial class ShiftItem : ObservableObject {
        [ObservableProperty]
        private string? shiftType;

        [ObservableProperty]
        private string? startTime;

        [ObservableProperty]
        private string? endTime;
    }
}