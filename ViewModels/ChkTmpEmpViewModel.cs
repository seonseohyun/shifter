using CommunityToolkit.Mvvm.ComponentModel;
using Shifter.Models;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;

namespace Shifter.ViewModels {
    public partial class ChkTmpEmpViewModel : ObservableObject {

        /** Constructor **/
        public ChkTmpEmpViewModel(Session? session, EmpModel? empModel) {
            _session  = session!;
            _empModel = empModel!;

            TeamName = _session?.GetCurrentTeamName();
            _ = UpdateTempEmpInfoAsync();
        }



        /** Member Variables **/
        private readonly Session ? _session;
        private readonly EmpModel? _empModel;
        [ObservableProperty] private ObservableCollection<Employee> tempEmpInfo = new();
        [ObservableProperty] private string? teamName = "";



        /** Member Methods **/
        public async Task UpdateTempEmpInfoAsync() {
            Console.WriteLine("[ChkTmpEmpViewModel] Executed UpdateTempEmpInfoAsync");
            
            ObservableCollection<Employee> ResultTempEmpInfo = new();
 
            ResultTempEmpInfo = await _empModel!.ChkTempStaffInfoAsync();

            TempEmpInfo = ResultTempEmpInfo;

            return;
        }
    }
}