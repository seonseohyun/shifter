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
using Shifter.Enums;

namespace Shifter.ViewModels {
    public partial class MngEmpViewModel : ObservableObject {

        /** Constructor **/
        public MngEmpViewModel(Session? session, EmpModel? empModel) {
            _session = session;
            _empModel = empModel;
            Grades = new ObservableCollection<GradeItem>(_session!.Grades);

            _ = UpdateEmpInfoList();
        }



        /** Member Variables **/
        private readonly Session? _session;
        private readonly EmpModel? _empModel;
        [ObservableProperty] private ObservableCollection<GradeItem> grades = [];
        [ObservableProperty] private ObservableCollection<Employee>  emps   = [];



        /** Member Methods **/

        /* Update Employee Information List (xaml Binded Variable) */
        private async Task UpdateEmpInfoList() {
            
            Emps.Clear(); // Clear the existing list before updating

            Emps = await _empModel!.ReqStaffListAsync();
        }


        /* Go To Check Temporary Employee Information Command */
        [RelayCommand] private void GoToChkTmpEmpInfo() {
            Console.WriteLine("[MngEmpViewModel] GoToChkTmpEmpInfo Executed");
            // Navigate to the temporary employee info view
            WeakReferenceMessenger.Default.Send(new PageChangeMessage(PageType.ChkTmpEmpInfo));
        }
    }
}
