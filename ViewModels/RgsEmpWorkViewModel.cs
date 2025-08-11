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
        public RgsEmpWorkViewModel(Session? session, EmpModel empmodel) {
            _session = session;
            _empmodel = empmodel;
        }


        /** Member Variables **/
        private readonly Session? _session;
        private readonly EmpModel? _empmodel;
        [ObservableProperty] private ObservableCollection<ShiftItem> shifts = new();
        [ObservableProperty] private string? selectedIndustry;
        [ObservableProperty] private string? companyName = "";
        [ObservableProperty] private string? teamName = "";


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
            Console.WriteLine("[RgsEmpWorkViewModel] GoToRgsEmpGrade Executed");

            if( string.IsNullOrEmpty(CompanyName) || string.IsNullOrEmpty(TeamName) || string.IsNullOrEmpty(SelectedIndustry) ) {
                MessageBox.Show("회사를 선택해주세요.", "Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            if( Shifts.Count == 0 ) {
                MessageBox.Show("근무정보를 입력해주세요.", "Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            // Check if all shifts have valid start and end times

            foreach( var shift in Shifts ) {
                if( string.IsNullOrEmpty(shift.StartTime) || string.IsNullOrEmpty(shift.EndTime)) {
                    MessageBox.Show("모든 근무시간을 입력해주세요.", "Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }
            }

            // Proceed with sending the team info

            Console.WriteLine("[RgsEmpWorkViewModel] Sending team info to server...");
            Console.WriteLine($"Company: {CompanyName}, Team: {TeamName}, Industry: {SelectedIndustry}");
            Console.WriteLine("[RgsEmpWorkViewModel] Shifts:");
            foreach( var shift in Shifts ) {
                Console.WriteLine($"Shift Type: {shift.ShiftType}, Start: {shift.StartTime}, End: {shift.EndTime}");
            }

            // Call the EmpModel method to send the team info
            if( _empmodel == null ) {
                MessageBox.Show("EmpModel is not initialized.", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            } else {
                _ = _empmodel!.RgsTeamInfoAsync(CompanyName, TeamName, SelectedIndustry, Shifts);
            }

            WeakReferenceMessenger.Default.Send(new PageChangeMessage(Enums.PageType.RgsEmpGrade));
        }
    }
}