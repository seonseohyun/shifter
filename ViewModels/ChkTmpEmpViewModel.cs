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
        public ChkTmpEmpViewModel(Session? session) {
            _session = session;

            UpdateTempEmpInfoAsync();
        }



        /** Member Variables **/
        private readonly Session? _session;
        [ObservableProperty] private ObservableCollection<TempEmpInfo> tempEmpInfo = new();



        /** Member Methods **/
        public async Task UpdateTempEmpInfoAsync() {
            Console.WriteLine("[ChkTmpEmpViewModel] Executed UpdateTempEmpInfoAsync");
            
            ObservableCollection<TempEmpInfo> ResultTempEmpInfo = new();

            /***********************************<Test>***********************************/

            TempEmpInfo TestTempEmpInfo = new()
            {
                TeamName      = "Test Team",
                EmpName       = "Test Name",
                EmpPhoneNum   = "010-0000-0000",
                EmpTotalHours = 80,
                EmpTmpId      = "Test ID",
                EmpTmpPw      = "Test Pw"
            };
            ResultTempEmpInfo.Clear();
            for( int i = 0; i < 15; i++ ) {
                ResultTempEmpInfo.Add(TestTempEmpInfo);
            }

            /*****************************************************************************/

            /* ResultTempEmpInfo = Model.GetTempEmpInfoAsync() */

            TempEmpInfo = ResultTempEmpInfo;

            return;
        }
    }


    /*** TempEmpInfo Class ***/
    public partial class TempEmpInfo : ObservableObject {

        /** Member Variables **/
        [ObservableProperty] private string? teamName      = "";
        [ObservableProperty] private string? empName       = "";
        [ObservableProperty] private string? empPhoneNum   = "";
        [ObservableProperty] private float ? empTotalHours = 0;
        [ObservableProperty] private string? empTmpId      = "";
        [ObservableProperty] private string? empTmpPw      = "";
    }
}